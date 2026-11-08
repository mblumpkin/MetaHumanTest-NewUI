"""
ue_import_textures.py  (runs INSIDE Unreal's Python, not regular Python)
=====================

Imports every PNG in SourceArt/Figma/UE into the project as UI textures:
    /Game/UserInterface/IHPC/Textures/T_IHPC_*.uasset

How to run it (editor closed), from the project folder:
    "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" ^
        "%CD%/MetaHumanTest.uproject" -run=pythonscript -script="%CD%/Tools/FigmaUI/ue_import_textures.py" ^
        -unattended -nosplash -nullrhi -SCCProvider=None

Or with the editor open: Tools > Execute Python Script... and pick this file.

Re-running it replaces the textures with the latest PNGs (after make_ui_textures.py).
"""

import os

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SOURCE_DIR = os.path.join(PROJECT_DIR, "SourceArt", "Figma", "UE")
DEST_PATH = "/Game/UserInterface/IHPC/Textures"


def import_textures():
    pngs = sorted(f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(".png"))
    unreal.log("[IHPC] Importing {} textures from {}".format(len(pngs), SOURCE_DIR))

    tasks = []
    for file_name in pngs:
        task = unreal.AssetImportTask()
        task.filename = os.path.join(SOURCE_DIR, file_name)
        task.destination_path = DEST_PATH
        task.destination_name = os.path.splitext(file_name)[0]   # T_IHPC_Toggle_On.png -> T_IHPC_Toggle_On
        task.automated = True          # no pop-up dialogs
        task.replace_existing = True   # re-running updates the textures
        task.save = False              # saved below, after the UI settings are applied
        tasks.append(task)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    for task in tasks:
        for object_path in task.imported_object_paths:
            texture = unreal.load_asset(object_path)
            if not isinstance(texture, unreal.Texture2D):
                continue
            # UI textures: full quality RGBA (no compression), "UI" texture group, sRGB.
            # The PNGs are 3-4x bigger than they are drawn, so they MUST have mipmaps + trilinear filtering,
            # otherwise shrinking them on screen makes thin lines and edges look pixelated / jagged.
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
            texture.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE)
            texture.set_editor_property("filter", unreal.TextureFilter.TF_TRILINEAR)
            texture.set_editor_property("never_stream", True)
            texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
            texture.set_editor_property("srgb", True)
            unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
            unreal.log("[IHPC] Imported {}".format(object_path))


import_textures()
