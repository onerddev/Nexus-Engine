#include "plugin_loader.hpp"
#include <iostream>
#include <dlfcn.h>

namespace nexus {

PluginLoader::PluginLoader() : plugin_dir_("./plugins") {}

PluginLoader::~PluginLoader() {
    for (auto& [name, plugin] : plugins_) {
        if (plugin.instance) {
            plugin.instance->shutdown();
        }
        if (plugin.handle) {
            dlclose(plugin.handle);
        }
    }
}

bool PluginLoader::load_plugin(const std::string& plugin_path) {
    void* handle = dlopen(plugin_path.c_str(), RTLD_LAZY | RTLD_LOCAL);
    if (!handle) {
        std::cerr << "[PluginLoader] Failed to load plugin: " << dlerror() << std::endl;
        return false;
    }
    
    typedef std::unique_ptr<Plugin>(*CreateFunc)();
    CreateFunc create = reinterpret_cast<CreateFunc>(dlsym(handle, "create_plugin"));
    
    if (!create) {
        std::cerr << "[PluginLoader] Failed to find create_plugin symbol" << std::endl;
        dlclose(handle);
        return false;
    }
    
    auto plugin = create();
    if (!plugin) {
        dlclose(handle);
        return false;
    }
    
    auto metadata = plugin->get_metadata();
    plugin->initialize();
    
    plugins_[metadata.name] = LoadedPlugin{std::move(plugin), handle, false};
    
    std::cout << "[PluginLoader] Loaded plugin: " << metadata.name << std::endl;
    return true;
}

bool PluginLoader::unload_plugin(const std::string& plugin_name) {
    auto it = plugins_.find(plugin_name);
    if (it == plugins_.end()) {
        return false;
    }
    
    auto& plugin = it->second;
    if (plugin.instance) {
        plugin.instance->shutdown();
    }
    
    if (plugin.handle) {
        dlclose(plugin.handle);
    }
    
    plugins_.erase(it);
    std::cout << "[PluginLoader] Unloaded plugin: " << plugin_name << std::endl;
    return true;
}

bool PluginLoader::reload_plugin(const std::string& plugin_name) {
    auto it = plugins_.find(plugin_name);
    if (it == plugins_.end()) {
        return false;
    }
    
    std::string path = plugin_name + ".so";
    unload_plugin(plugin_name);
    return load_plugin(path);
}

Plugin* PluginLoader::get_plugin(const std::string& plugin_name) {
    auto it = plugins_.find(plugin_name);
    if (it != plugins_.end()) {
        return it->second.instance.get();
    }
    return nullptr;
}

std::vector<std::string> PluginLoader::list_plugins() const {
    std::vector<std::string> names;
    for (const auto& [name, _] : plugins_) {
        names.push_back(name);
    }
    return names;
}

bool PluginLoader::execute_plugin(const std::string& plugin_name) {
    auto plugin = get_plugin(plugin_name);
    if (!plugin) {
        return false;
    }
    
    plugin->execute();
    return true;
}

void PluginLoader::pause_plugin(const std::string& plugin_name) {
    auto it = plugins_.find(plugin_name);
    if (it != plugins_.end()) {
        it->second.active = false;
    }
}

void PluginLoader::resume_plugin(const std::string& plugin_name) {
    auto it = plugins_.find(plugin_name);
    if (it != plugins_.end()) {
        it->second.active = true;
    }
}

std::string PluginLoader::get_plugin_status(const std::string& plugin_name) const {
    auto it = plugins_.find(plugin_name);
    if (it != plugins_.end() && it->second.instance) {
        return it->second.instance->get_status();
    }
    return "NOT_FOUND";
}

std::vector<Plugin::Metadata> PluginLoader::get_all_metadata() const {
    std::vector<Plugin::Metadata> metadata_list;
    for (const auto& [_, plugin] : plugins_) {
        if (plugin.instance) {
            metadata_list.push_back(plugin.instance->get_metadata());
        }
    }
    return metadata_list;
}

} // namespace nexus
