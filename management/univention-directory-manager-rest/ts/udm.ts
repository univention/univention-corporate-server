import axios from 'axios';
import { parse } from 'uri-template';

//class Client {
//  client: Session;
//
//  constructor(client: Session) {
//    this.client = client;
//  }
//}

interface Property {
    layout: Array<string>;
    advanced: boolean;
    description: string;
    label: string;
    is_app_tab: boolean;
    help: string;
}

class NoModule extends Error {}

class NoURI extends Error {}

class NotFound extends Error {}

interface Link {
  title: string,
  href: string,
}

interface HAL {
  _links: Record<string, Array<Link>>;
  _embedded: Record<string, Array<Link>>;
}

interface Representation {
  dn: string;
  uuid: string;
  uri: string;
  objectType: string;
  id: string; // null?
  position: string; // null?
  options: Record<string, boolean>;
  properties: Record<string, unknown>;
  policies: Record<string, Array<string>>;
  superordinate: string; // null?
}

type UDMData = HAL & Representation;

function resolveRelation(link: string, template: Record<string, unknown>): string {
  const tpl = parse(link);
  return tpl.expand(template);
}

class Base {
  _links: Array<Link> = [];

  protected async resolveRelation(relation: string, template: Record<string, unknown> = {}): Promise<string> {
    await this.load();
    const link = this._links[relation][0].href;
    return resolveRelation(this._links[relation][0].href, template);
  }

  protected async resolveNamedRelation(relation: string, name: string, template: Record<string, unknown> = {}): Promise<string> {
    await this.load();
    const link = this._links[relation].find((rel) => rel.name === name).href;
    return resolveRelation(link, template);
  }

  protected async load() {
    if (this._links.length === 0) {
      await this.reload();
    }
  }

  async reload() {
  }
}

export class UDM extends Base {
  version: number;
  uri: string;
  axios: any;
  entry: any = null;
  modules: Array<UDMModule>;

  constructor(uri: string, username: string, password: string, version: number = 1) {
    super();
    this.version = version;
    this.modules = [];
    this.uri = uri;
    this.axios = axios.create({
      timeout: 10000,
      headers: {
        'X-Requested-With': 'XMLHTTPRequest',
        'Accept': 'application/hal+json; q=1, application/json; q=0.9; text/html; q=0.2, */*; q=0.1',
        'Accept-Language': 'en-US',
        'User-Agent': 'udm.js/1.0',
      },
      auth: { username, password },
    });
  }

  async reload() {
    this.modules = [];
    this.entry = (await this.axios.get(this.uri)).data;
    this._links = this.entry._links;
  }

  async getLdapBase(): Promise<string> {
    const uri = await this.resolveRelation('udm:ldap-base');
    const resp = await this.axios.get(uri);
    return (new UDMObject(this, resp.data, null, null)).dn;
  }

  async getModules(): Promise<Array<UDMModule>> {
    await this.load();
    if (this.modules.length === 0) {
      const modulesLinks = this.entry._links['udm:object-modules'];
      for (const moduleLink of modulesLinks) {
        const baseMod = (await this.axios.get(moduleLink.href)).data;
        baseMod._links['udm:object-types'].forEach((mod) => {
          this.modules.push(new UDMModule(this, mod.name, mod.title, mod.href));
        });
      };
    }
    return this.modules;
  }

  async get(name: string): Promise<UDMModule | undefined> {
    return (await this.getModules()).find((mod) => mod.id === name);
  }

  async getObject(objectType: string, dn: string): Promise<UDMObject> {
    const module = await this.get(objectType);
    assertModuleIsFound(module);
    return await module.get(dn);
  }

  async objByDn(dn: string): Promise<UDMObject> {
    const uri = await this.resolveRelation('udm:object/get-by-dn', { dn });
    return this.objFromUri(uri);
  }

  async objByUuid(uuid: string): Promise<UDMObject> {
    const uri = await this.resolveRelation('udm:object/get-by-uuid', { uuid });
    return this.objFromUri(uri);
  }

  async objFromUri(uri: string): Promise<UDMObject> {
    const resp = await this.axios.get(uri);
    return new UDMObject(this, resp.data, resp.headers.etag, resp.headers['last-modified']);
  }
}

class UDMModule extends Base {
  private udm: UDM;
  readonly id: string;
  readonly title: string;
  readonly uri: string;

  constructor(udm: UDM, id: string, title: string, uri: string) {
    super();
    this.udm = udm;
    this.id = id;
    this.title = title;
    this.uri = uri;
  }

  async reload() {
    const response = await this.udm.axios.get(this.uri);
    this._links = response.data._links;
  }

  async new(position?: string, superordinate?: string, template?: string): Promise<UDMObject> {
    const data = { position, superordinate, template };
    const uri = await this.resolveRelation('create-form', data);
    const resp = await this.udm.axios.get(uri);
    return new UDMObject(this.udm, resp.data, null, null);
  }

  async get(dn: string): Promise<UDMObject> {
    const objs = await this.search('objectClass=*', { position: dn, scope: 'base', properties: 'dn' });
    if (objs.length > 0) {
      const obj = objs[0];
      await obj.reload();
      return obj;
    }
    throw new NotFound('Wrong object type!?');
  }

  async getByEntryUuid(uuid: string): Promise<UDMObject> {
    const objs = await this.search(`entryUUID=${uuid}`, { properties: 'dn' });
    if (objs.length > 0) {
      const obj = objs[0];
      await obj.reload();
      return obj;
    }
    throw new NotFound('Wrong object type!?');
  }

  async search(filter: string, template: Record<string, unknown>): Promise<Array<UDMObject>> {
    const newTemplate = { ...template, filter };
    const uri = await this.resolveRelation('search', newTemplate);
    const response = await this.udm.axios.get(uri);
    if (! response.data._embedded['udm:object']) {
      return [];
    }
    return response.data._embedded['udm:object'].map((obj) => new UDMObject(this.udm, obj, null, null));
  }

  async getLayout() {
    const uri = await this.resolveRelation('udm:layout');
    const response = await this.udm.axios.get(uri);
    return response.data.layout;
  }

  async getProperties(): Promise<Array<Property>> {
    const uri = await this.resolveRelation('udm:properties');
    const response = await this.udm.axios.get(uri);
    return response.data.properties;
  }

  async getPropertyChoices(property: string) {
    const uri = await this.resolveRelation('udm:properties');
    const response = await this.udm.axios.get(uri);
    for (const link of response.data._links['udm:property-choices']) {
      if (link.name === property) {
        const response = await this.udm.axios.get(link.href);
        return response.data.choices;
      }
    };
  }

  async policyResult(module: string, position: string, policy: string) {
    const uri = await this.resolveNamedRelation('udm:policy-result', module, { position, policy });
    // TODO
  }

  async getReportTypes(): Promise<Array<string>> {
    await this.load();
    return this._links['udm:report'].map((reportType) => reportType.name).filter((reportType) => reportType);
  }

  async createReport(reportType: string, dns: Array<string>) {
    const uri = await this.resolveNamedRelation('udm:report', reportType, { dn: dns });
    const response = await this.udm.axios.get(uri);
    return response.data;
  }
}

class UDMObject {
  private udm: UDM;
  private representation: Representation;
  private hal: HAL;
  private etag: string | null;
  private lastModified: string | null;

  constructor(udm: UDM, data: UDMData, etag: string | null, lastModified: string | null) {
    this.udm = udm;
    this.representation = data;
    this.hal = data;
    this.etag = etag;
    this.lastModified = lastModified;
  }

  get properties(): Record<string, unknown> {
    return this.representation.properties;
  }

  get uuid(): string {
    return this.representation.uuid;
  }

  get dn(): string {
    return this.representation.dn;
  }

  get uri(): string | undefined {
    return this.hal._links.self?.[0]?.href;
  }

  get objectType(): string {
    return this.representation.objectType;
  }

  get options(): Record<string, boolean> {
    return this.representation.options;
  }

  get policies(): Record<string, Array<string>> {
    return this.representation.policies;
  }

  get superordinate(): string {
    return this.representation.superordinate;
  }

  private set_uri(uri: string) {
    const links = this.hal._links;
    if (links.self && links.self[0]) {
      links.self[0].href = uri;
    } else {
      links.self = [{ title: 'self', href: uri }];
    }
  }

  async reload() {
    assertUriIsString(this.uri);
    const obj = await this.udm.objFromUri(this.uri);
    this.representation = obj.representation;
    this.hal = obj.hal;
    this.etag = obj.etag;
    this.lastModified = obj.lastModified;
  }

  async save() {
    if (this.dn) {
      await this.modify();
    } else {
      await this.create();
    }
  }

  async delete() {
    /*
     * object may not be used after delete
     */
    //assert(this.uri);
    await this.udm.axios.delete(this.uri);
  }

  async move(position: string) {
    //assert(this.uri);
    this.representation.position = position;
    await this.modify();
  }

  private async modify() {
    const headers = {
      'If-Unmodified-Since': this.lastModified,
      'If-Match': this.etag,
    };
    const response = await this.udm.axios.put(this.uri, this.representation, headers);
    this.set_uri(response.headers.location);
    await this.reload();
  }

  private async create() {
    const uri = this.hal._links.create[0].href;
    const response = await this.udm.axios.post(uri, this.representation);
    this.set_uri(response.headers.location);
    await this.reload();
  }

  async generateServiceSpecificPassword(service: string): Promise<string> {
    const uri = this.hal._links['udm:service-specific-password'][0].href;
    const response = await this.udm.axios.post(uri, { service });
    return response.data.password;
  }
}


function assertModuleIsFound(value: UDMModule | undefined): asserts value is UDMModule {
    if (value instanceof UDMModule) {
      throw new NoModule('No module found.');
    }
}

function assertUriIsString(value: string | undefined): asserts value is string {
    if (typeof value !== 'string') {
      throw new NoURI('No URI set.');
    }
}
