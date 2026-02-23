#pragma once

#include <cstdint>
#include <string>
#include <memory>
#include <map>
#include <functional>
#include <vector>

namespace nexus {

/**
 * @class Plugin
 * @brief Base interface for loadable plugins
 */
class Plugin {
public:
    struct Metadata {
        std::string name;
        std::string version;
        std::string author;
        std::string description;
    };

    virtual ~Plugin() = default;
    
    virtual Metadata get_metadata() const = 0;
    virtual void initialize() = 0;
    virtual void shutdown() = 0;
    virtual void execute() = 0;
    virtual std::string get_status() const = 0;
};

/**
 * @class PluginLoader
 * @brief Dynamic plugin loading and management system
 * 
 * Features:
 * - Dynamic shared library loading (.so/.dll)
 * - Plugin registration and lifecycle
 * - Dependency resolution
 * - Error handling with rollback
 * 
 * Thread-safe: Partial (loading must be synchronized)
 */
class PluginLoader {
public:
    using PluginFactory = std::function<std::unique_ptr<Plugin>()>;
    
    PluginLoader();
    ~PluginLoader();
    
    // Plugin management
    bool load_plugin(const std::string& plugin_path);
    bool unload_plugin(const std::string& plugin_name);
    bool reload_plugin(const std::string& plugin_name);
    
    // Plugin registry
    Plugin* get_plugin(const std::string& plugin_name);
    std::vector<std::string> list_plugins() const;
    
    // Plugin execution
    bool execute_plugin(const std::string& plugin_name);
    void pause_plugin(const std::string& plugin_name);
    void resume_plugin(const std::string& plugin_name);
    
    // Status
    std::string get_plugin_status(const std::string& plugin_name) const;
    std::vector<Plugin::Metadata> get_all_metadata() const;

private:
    struct LoadedPlugin {
        std::unique_ptr<Plugin> instance;
        void* handle = nullptr;
        bool active = false;
    };

    std::map<std::string, LoadedPlugin> plugins_;
    std::string plugin_dir_;
};

} // namespace nexus
