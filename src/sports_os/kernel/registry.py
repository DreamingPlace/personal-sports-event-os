from importlib.metadata import entry_points
from .data import KernelError
from .contract import Module

class Registry:
    def __init__(self):
        self._modules={}

    def register(self, module, replace=False):
        if not isinstance(module,Module) or not module.module_id:
            raise KernelError('插件必须实现Module协议并提供module_id')
        if module.module_id in self._modules and not replace:
            raise KernelError('重复模块ID：'+module.module_id)
        self._modules[module.module_id]=module

    @classmethod
    def discover(cls):
        registry=cls()
        for ep in sorted(entry_points(group='sports_os.modules'),key=lambda e:e.name):
            registry.register(ep.load()())
        return registry

    def get(self, module_id):
        try:return self._modules[module_id]
        except KeyError:raise KernelError('未安装模块：'+module_id) from None

    def list(self):
        return [dict(module_id=m.module_id,module_version=m.module_version,schema_version=m.schema_version,
                     dependencies=list(m.dependencies),optional_dependencies=list(m.optional_dependencies),
                     provides=list(m.provides),requires_capabilities=list(m.requires_capabilities))
                for _,m in sorted(self._modules.items())]

    def order(self, enabled):
        enabled=set(enabled);graph={}
        for key in sorted(enabled):
            m=self.get(key);missing=set(m.dependencies)-enabled
            if missing:raise KernelError(f'{key} 缺依赖 {sorted(missing)}')
            deps=set(m.dependencies)|(set(m.optional_dependencies)&enabled)
            for cap in m.requires_capabilities:
                providers=[k for k in enabled if cap in self.get(k).provides]
                if len(providers)!=1:raise KernelError(f'{key}: 能力 {cap} 提供者必须唯一：{providers}')
                deps.add(providers[0])
            graph[key]=deps
        caps={}
        for key in sorted(enabled):
            for cap in self.get(key).provides:
                if cap in caps:raise KernelError(f'能力冲突 {cap}: {caps[cap]}, {key}')
                caps[cap]=key
        result=[];visiting=set();done=set()
        def visit(key):
            if key in visiting:raise KernelError('模块依赖循环：'+key)
            if key in done:return
            visiting.add(key)
            for dep in sorted(graph[key]):visit(dep)
            visiting.remove(key);done.add(key);result.append(key)
        for key in sorted(enabled):visit(key)
        return result
