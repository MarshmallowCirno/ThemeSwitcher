# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import os

import bpy
from bpy.props import CollectionProperty, IntProperty, StringProperty
from bpy.types import AddonPreferences, Operator, Panel, PropertyGroup, UIList
from bpy.utils import register_class, unregister_class


bl_info = {
    "name": "Theme Switcher",
    "author": "MarshmallowCirno",
    "blender": (3, 3, 1),
    "version": (1, 1),
    "location": "3D View > Sidebar > View",
    "description": "Fast switching between themes with Ctrl+Wheel",
    "category": "Interface",
    "doc_url": "https://gumroad.com/l/PsTugR",
    "tracker_url": "https://blenderartists.org/t/theme-switcher/1211787",
}


class TSWITCH_UL_themes(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        layout.label(text=item.name)


class TSWITCH_OT_reload(Operator):
    bl_idname = "theme_switcher.reload"
    bl_label = "Reload Themes"
    bl_description = "Reload list of themes"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        addon_prefs = context.preferences.addons[__name__].preferences

        # Backup active theme name.
        if addon_prefs.themes:
            idx = addon_prefs.active_theme_index
            init_active_theme_name = addon_prefs.themes[idx].name
        else:
            init_active_theme_name = None

        # Clear theme collection.
        addon_prefs.themes.clear()

        # Get theme xmls.
        xmls = collect_xmls()

        # Add themes to collection.
        import_themes(xmls)

        # Restore active theme or reset index.
        active_theme_index = 0
        if init_active_theme_name is not None:
            # If current active theme was deleted set active index to 0.
            init_active_theme_index = addon_prefs.themes.find(init_active_theme_name)
            active_theme_index = max(init_active_theme_index, 0)

        addon_prefs.active_theme_index = active_theme_index
        return {'FINISHED'}


def collect_xmls() -> list[tuple[str, str]]:
    """Get xml files in directory path and return their names and paths."""
    theme_dir_paths = bpy.utils.preset_paths("interface_theme")
    xmls = []
    for dir_path in theme_dir_paths:
        xml_names = os.listdir(dir_path)
        xmls.extend([(xml_name, os.path.join(dir_path, xml_name)) for xml_name in xml_names])
    xmls.sort()
    return xmls


def import_themes(xmls: list[tuple[str, str]]) -> None:
    """Fill addon properties with names and paths of xmls."""
    addon_prefs = bpy.context.preferences.addons[__name__].preferences

    for xml_name, xml_path in xmls:
        theme = addon_prefs.themes.add()
        theme.path = xml_path

        # Underscores to whitespaces.
        name = xml_name.replace("_", " ")
        # CamelCase.
        name = name.title()
        # Remove extension.
        if name.endswith(".Xml"):
            name = name[:-4]
        theme.name = name


class TSWITCH_OT_edit(Operator):
    bl_idname = "theme_switcher.edit"
    bl_label = "Edit Themes"
    bl_description = "Open theme editor"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        context.preferences.active_section = 'THEMES'
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        return {'FINISHED'}


class TSWITCH_PT_sidebar(Panel):
    bl_label = "Theme"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"

    def draw(self, context):
        layout = self.layout
        addon_prefs = context.preferences.addons[__name__].preferences

        col = layout.column(align=True)
        col.template_list("TSWITCH_UL_themes", "", addon_prefs, "themes", addon_prefs, "active_theme_index")

        row = col.row(align=True)
        row.operator("theme_switcher.reload", icon='FILE_REFRESH', text="Reload")
        row.operator("theme_switcher.edit", icon='COLOR', text="Edit")


def activate_theme(_, context):
    addon_prefs = context.preferences.addons[__name__].preferences
    active_theme_index = addon_prefs.active_theme_index
    active_theme_path = addon_prefs.themes[active_theme_index].path

    bpy.ops.script.execute_preset(filepath=active_theme_path, menu_idname="USERPREF_MT_interface_theme_presets")


class TSWITCH_PG_themes(PropertyGroup):
    # name = StringProperty() -> Instantiated by default
    path: StringProperty()


def update_sidebar_category(self, _):
    is_panel = hasattr(bpy.types, 'TSWITCH_PT_sidebar')
    if is_panel:
        try:
            bpy.utils.unregister_class(TSWITCH_PT_sidebar)
        except:  # noqa
            pass
    TSWITCH_PT_sidebar.bl_category = self.sidebar_category
    bpy.utils.register_class(TSWITCH_PT_sidebar)


class TSWITCH_preferences(AddonPreferences):
    bl_idname = __name__

    themes: CollectionProperty(
        type=TSWITCH_PG_themes,
    )
    active_theme_index: IntProperty(
        name="Active Index",
        description="Index of the currently active theme",
        default=0,
        update=activate_theme,
    )
    sidebar_category: StringProperty(
        name="Sidebar Category",
        description="Name for the tab in the sidebar panel",
        default="View",
        update=update_sidebar_category,
    )

    def draw(self, _):
        layout = self.layout

        col = layout.column()
        col.use_property_split = True
        col.use_property_decorate = False

        col.prop(self, "sidebar_category")


classes = (
    TSWITCH_UL_themes,
    TSWITCH_PT_sidebar,
    TSWITCH_OT_reload,
    TSWITCH_OT_edit,
    TSWITCH_PG_themes,
    TSWITCH_preferences,
)


def initialize_themes():
    addon_prefs = bpy.context.preferences.addons[__name__].preferences

    if not addon_prefs.themes:
        # Get theme xmls.
        xmls = collect_xmls()

        # Add themes to collection.
        import_themes(xmls)


def register():
    for cls in classes:
        register_class(cls)

    initialize_themes()


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
