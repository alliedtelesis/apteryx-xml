/**
 * @file lua.c
 * Lua bindings for using an XML schema with Apteryx.
 *
 * Copyright 2016, Allied Telesis Labs New Zealand, Ltd
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 3 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this library. If not, see <http://www.gnu.org/licenses/>
 */
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <syslog.h>
#include <lua.h>
#include <lauxlib.h>
#include <apteryx.h>
#include "apteryx-xml.h"

/* Debug */
static bool apteryx_xml_debug = false;
#define DEBUG(fmt, args...) \
    if (apteryx_xml_debug) \
    { \
        syslog (LOG_DEBUG, fmt, ## args); \
        printf (fmt, ## args); \
    }

/* Global pointer to the loaded schema */
static sch_instance *api = NULL;
/* A root user can write to read-only fields */
static bool is_root = true;

static int
lua_apteryx_debug (lua_State *L)
{
    if (lua_gettop (L) < 1 || !lua_isboolean (L, 1))
    {
        luaL_error (L, "Invalid arguments: requires boolean");
        return 0;
    }
    apteryx_xml_debug = lua_toboolean (L, 1);
    return 0;
}

/* Push either a value or table onto the stack */
static bool
push_node (lua_State *L, sch_instance *api, const char *path, const char *key)
{
    char *__path;
    sch_node *node;
    char *name;

    /* Lookup the node */
    __path = g_strdup_printf ("%s/%s", path, key);
    node = sch_lookup (api, __path);
    if (!node)
    {
        /* Not accessible at all */
        g_free (__path);
        luaL_error (L, "\'%s\' invalid", key);
        return false;
    }

    /* Use the real path name */
    name = sch_name (node);
    if (strcmp (name , "*") != 0)
    {
        free (__path);
        __path = g_strdup_printf ("%s/%s", path, name);
    }
    free (name);

    /* For leaves we return a value - either from db, default or nil */
    if (sch_is_leaf (node))
    {
        char *value;

        /* Make sure we have access */
        if (!is_root && !sch_is_readable (node))
        {
            /* Not readable */
            g_free (__path);
            luaL_error (L, "\'%s\' not readable", key);
            return false;
        }

        /* Get the value from Apteryx or its default */
        value = apteryx_get (__path);
        /* Pass back defined values if they exist in the schema */
        value = sch_translate_to (node, value);
        lua_pushstring (L, value);
        free (value);
    }
    else
    {
        /* Table on the stack */
        lua_newtable (L);
        lua_pushstring (L, "__path");
        lua_pushstring (L, __path);
        lua_rawset (L, -3);
        luaL_setmetatable (L, "apteryx_mt");
    }
    g_free (__path);
    return true;
}

static int
__index (lua_State *L)
{
    const char *path;
    const char *key;

    /* If no API, this key does not exist! */
    if (!api)
    {
        return 0;
    }

    /* Get stored parameters */
    luaL_checktype (L, 1, LUA_TTABLE);
    lua_pushstring (L, "__path");
    lua_rawget (L, 1);
    path = lua_tostring (L, -1);
    if (path == NULL)
    {
        path = "";
    }
    lua_pop (L, 1);

    /* Get passed in parameters */
    key = lua_tostring (L, 2);
    if (!key)
    {
        return 0;
    }

    DEBUG ("__index: %s/%s\n", path, key);

    /* Push the value onto the stack */
    if (!push_node (L, api, path, key))
    {
        return 0;
    }

    /* We are returning 1 item - either a table or value */
    return 1;
}

static int
__newindex (lua_State *L)
{
    const char *path;
    const char *key;
    const char *value;
    char *name;

    /* If no API, this key does not exist! */
    if (!api)
    {
        return 0;
    }

    /* Get stored parameters */
    luaL_checktype (L, 1, LUA_TTABLE);
    lua_pushstring (L, "__path");
    lua_rawget (L, 1);
    path = lua_tostring (L, -1);
    if (path == NULL)
    {
        path = "";
    }
    lua_pop (L, 1);

    /* Get passed in parameters */
    key = lua_tostring (L, 2);
    if (!key)
    {
        return 0;
    }
    value = lua_tostring (L, 3);

    DEBUG ("__newindex: %s/%s = %s\n", path, key, value);

    /* Validate the node */
    char *__path = g_strdup_printf ("%s/%s", path, key);
    sch_node *node = sch_lookup (api, __path);
    if (!node || (!is_root && !sch_is_writable (node)) || !sch_is_leaf (node))
    {
        /* Not accessible */
        g_free ((gpointer) __path);
        luaL_error (L, "\'%s\' not writable", key);
        return 0;
    }

    /* Use the real path name */
    name = sch_name (node);
    if (strcmp (name , "*") != 0)
    {
        free (__path);
        __path = g_strdup_printf ("%s/%s", path, name);
    }
    free (name);

    /* Translate from the schema version */
    char *val = sch_translate_from (node, g_strdup (value));
    lua_pushboolean (L, apteryx_set (__path, val));
    g_free (val);
    g_free (__path);
    return 1;
}

static int
__call (lua_State *L)
{
    const char *path;
    const char *key;
    const char *value;

    /* If no API, this key does not exist! */
    if (!api)
    {
        return 0;
    }

    /* Get stored parameters */
    luaL_checktype (L, 1, LUA_TTABLE);
    lua_pushstring (L, "__path");
    lua_rawget (L, 1);
    path = lua_tostring (L, -1);
    if (path == NULL)
    {
        path = "";
    }
    lua_pop (L, 1);

    /* Get passed in parameters */
    key = lua_tostring (L, 2);
    if (lua_isnil (L, 3))
        value = "";
    else
        value = lua_tostring (L, 3);

    if (value)
    {
        DEBUG ("__call: %s%s%s = %s\n", path, key ? "/" : "", key ? : "", value);
    }
    else
    {
        DEBUG ("__call: %s%s%s\n", path, key ? "/" : "", key ? : "");
    }

    /* Search or general access */
    if (!key)
    {
        char *__path = g_strdup_printf ("%s/", path);
        GList *paths = apteryx_search (__path);
        g_free (__path);
        int num = g_list_length (paths);
        GList *_iter = paths;
        lua_createtable (L, num, 0);
        for (int i = 1; i <= num; i++)
        {
            const char *path = (char *) _iter->data;
            lua_pushstring (L, strrchr (path, '/') + 1);
            lua_rawseti (L, -2, i);
            _iter = _iter->next;
        }
        g_list_free_full (paths, free);
    }
    else if (value)
    {
        /* Validate the node */
        char *__path = g_strdup_printf ("%s/%s", path, key);
        sch_node *node = sch_lookup (api, __path);
        if (!node || (!is_root && !sch_is_writable (node)) || !sch_is_leaf (node))
        {
            /* Not accessible */
            g_free ((gpointer) __path);
            luaL_error (L, "\'%s\' not writable", key);
            return 0;
        }

        /* Use the real path name */
        char *name = sch_name (node);
        if (strcmp (name , "*") != 0)
        {
            free (__path);
            __path = g_strdup_printf ("%s/%s", path, name);
        }
        free (name);

        /* Translate from the schema version */
        char *val = sch_translate_from (node, g_strdup (value));
        lua_pushboolean (L, apteryx_set (__path, val));
        g_free (val);
        g_free (__path);
        return 1;
    }
    else
    {
        /* Push the node/value onto the stack */
        if (!push_node (L, api, path, key))
        {
            return 0;
        }
    }

    /* We are returning 1 item - either a table or value */
    return 1;
}

static int
lua_apteryx_api (lua_State *L)
{
    /* Metatable functions */
    static const luaL_Reg _apteryx_mt[] = {
        { "__index", __index },
        { "__newindex", __newindex },
        { "__call", __call },
        { NULL, NULL }
    };
    const char *path = ".";
    if (lua_gettop (L) == 1 && lua_isstring (L, 1))
    {
        path = lua_tostring (L, 1);
    }

    /* Cleanup old one */
    if (api)
    {
        sch_free (api);
    }

    /* Parse XML files in the specified directory */
    api = sch_load (path);
    if (!api)
    {
        /* No good */
        luaL_error (L, "Error loading: schema from \"%s\"", path);
        return 0;
    }

    /* Create the API object */
    luaL_newmetatable (L, "apteryx_mt");
    luaL_setfuncs (L, _apteryx_mt, 0);
    luaL_newmetatable (L, "apteryx_api");
    luaL_setmetatable (L, "apteryx_mt");
    lua_pushstring (L, "__path");
    lua_pushstring (L, "");
    lua_rawset (L, -3);
    return 1;
}

static int
lua_apteryx_valid (lua_State *L)
{
    if (lua_gettop (L) != 1 || !lua_isstring (L, 1))
    {
        luaL_error (L, "Invalid arguments: requires path");
        return 0;
    }

    /* If no API, this path does not exist! */
    if (api && sch_lookup (api, lua_tostring (L, 1)))
    {
        /* All good */
        lua_pushboolean (L, true);
        return 1;
    }

    /* No good */
    lua_pushboolean (L, false);
    return 1;
}

int
luaopen_libapteryx_xml (lua_State *L)
{
    /* Standard functions */
    static const luaL_Reg _apteryx_fns[] = {
        { "debug", lua_apteryx_debug },
        { "api", lua_apteryx_api },
        { "valid", lua_apteryx_valid },
        { NULL, NULL }
    };

    /* Initialise Apteryx */
    if (!apteryx_init (false))
    {
        return 0;
    }

    /* Return the Apteryx object on the stack */
    luaL_newmetatable (L, "apteryx");
    luaL_setfuncs (L, _apteryx_fns, 0);
    return 1;
}

int
luaopen_apteryx_xml (lua_State *L)
{
    return luaopen_libapteryx_xml (L);
}

int
luaopen_xml (lua_State *L)
{
    return luaopen_libapteryx_xml (L);
}
