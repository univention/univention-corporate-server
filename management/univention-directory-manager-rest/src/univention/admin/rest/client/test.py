import asyncio

from univention.admin.rest.client.aclient import UDM


async def main():
    uri = 'http://localhost/univention/udm/'
    async with UDM.http(uri, 'Administrator', 'univention') as udm:
        module = await udm.get("users/user")
        print(module)
        objs = module.search('uid=demo_student')
        print(objs)
        #obj = anext(objs)
        #if obj:
        #    print(obj)
        #    #obj = await obj
        #    obj = await obj.open()
        #print('Object {}'.format(obj))
        async for obj in objs:
            if obj:
                obj = await obj.open()
            print('Object {}'.format(obj))
            print(obj.uri)
            print(await obj.module)
            for group in obj.objects.groups:
                g = await group.open()
                print(g)
            obj.properties['description'] = 'muhahaha'
            await obj.save()

            return


asyncio.run(main())
