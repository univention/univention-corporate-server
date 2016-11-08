from univention.management.console import Translation
from univention.management.console.modules import Base, UMC_OptionMissing

from .ldap import UDM_Module

_ = Translation('univention-management-console-modules-udm').translate


class Instance(Base):

  def query(self, request):
    pass

  def containers(self, request):
      module_name = request.options.get('objectType')
      if not module_name or 'all' == module_name:
        module_name = request.flavor
      if not module_name:
        raise UMC_OptionMissing('No valid module name found')

      module = UDM_Module(module_name)
      self.finished(
        request.id,
        module.containers + self.settings.containers(request.flavor))
