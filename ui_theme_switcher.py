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


bl_info = {
    "name":         "Theme Switcher",
    "author":       "MarshmallowCirno",
    "blender":      (2, 80, 0),
    "version":      (1, 0),
    "location":     "3D View > Sidebar > View",
    "description":  "Quick switching between themes with Ctrl+Wheel",
    "category":     "Interface"
}


import bpy, os
from bpy.props import IntProperty, StringProperty, CollectionProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup, UIList, Scene


class TSWITCH_UL_themes(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)


class TSWITH_OT_reload(Operator):
    bl_idname = "theme_switcher.reload"
    bl_label = "Reload Themes"
    bl_description = "Reload list of themes"
    bl_options = {'INTERNAL'}
  
    def invoke(self, context, event):
        scene = context.scene
        themes = scene.theme_switcher.themes
        
        # backup active theme name
        if scene.theme_switcher.themes:
            active_theme_index = scene.theme_switcher.active_theme_index
            init_active_theme_name = themes[active_theme_index].name
        else:
            init_active_theme_name = ""
        
        # clear theme collection
        scene.theme_switcher.themes.clear()
        
        # get theme xmls
        theme_dir_pathes = bpy.utils.preset_paths("interface_theme")
        xmls = []
        for dir_path in theme_dir_pathes:
            xmls.extend(self.get_xmls(scene, dir_path))
        xmls.sort(key=lambda x: x[0])
        
        # add themes to collection
        self.import_themes(scene, xmls)
        
        # restore active theme
        if init_active_theme_name:
            init_active_theme_index = max(themes.find(init_active_theme_name), 0) # if theme was deleted, then set active index to 0
            scene.theme_switcher.active_theme_index = init_active_theme_index
        return {'FINISHED'}
        
    @staticmethod
    def get_xmls(scene, dir_path):
        xml_names = os.listdir(dir_path)
        xmls = [(xml_name, os.path.join(dir_path, xml_name)) for xml_name in xml_names]
        return xmls
            
    @staticmethod
    def import_themes(scene, xmls):
        for xml_name, xml_path in xmls:
            theme = scene.theme_switcher.themes.add()
            theme.path = xml_path
            
            name = xml_name.replace("_", " ")
            if name.endswith(".xml"):
                name = name[:-4]
            theme.name = name.title() # CamelCase
            

class TSWITH_OT_edit(Operator):
    bl_idname = "theme_switcher.edit"
    bl_label = "Edit Themes"
    bl_description = "Open theme editor"
    bl_options = {'INTERNAL'}
            
    def invoke(self, context, event):
        context.preferences.active_section = 'THEMES'
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        return {'FINISHED'}


class TSWITH_PT_sidebar(Panel):
    bl_label = "Theme"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.template_list("TSWITCH_UL_themes", "", scene.theme_switcher, "themes", scene.theme_switcher, "active_theme_index")

        sub = row.column(align=True)
        sub.operator("theme_switcher.reload", icon='FILE_REFRESH', text="")
        sub.operator("theme_switcher.edit", icon='COLOR', text="")


def activate_theme(self, context):
    scene = context.scene
    active_theme_index = scene.theme_switcher.active_theme_index
    active_theme_path = scene.theme_switcher.themes[active_theme_index].path
    
    bpy.ops.script.execute_preset(filepath=active_theme_path, menu_idname="USERPREF_MT_interface_theme_presets")


class TSWITH_PG_themes(PropertyGroup):
    # name = StringProperty() -> Instantiated by default
    path: StringProperty()


class TSWITH_PG_scene(PropertyGroup):
    # name = StringProperty() -> Instantiated by default
    themes: CollectionProperty(type=TSWITH_PG_themes)
    active_theme_index: IntProperty(
        name="Active Index", 
        description="Index of the currently active theme",
        default=0, 
        update=activate_theme)


classes = (
    TSWITCH_UL_themes,
    TSWITH_PT_sidebar,
    TSWITH_OT_reload,
    TSWITH_OT_edit,
    TSWITH_PG_themes,
    TSWITH_PG_scene
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    Scene.theme_switcher = PointerProperty(type=TSWITH_PG_scene)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del Scene.theme_switcher


if __name__ == "__main__":
    register()
