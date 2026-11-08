"""
build_widget_blueprints.py
==========================

RECORD of how the IHPC Widget Blueprints were built (2026-11-07).

These are the exact steps that were sent to the Unreal Editor through the
Unreal MCP "ProgrammaticToolset" (execute_tool_script). It is kept here so the
team can see every widget, size, colour and font that was set, and could rebuild
a Widget Blueprint from scratch if needed.

You do NOT need to run this - the Widget Blueprints already exist in
/Game/UserInterface/IHPC/Widgets and can be edited normally in the UMG designer.
To rebuild one, delete the asset first (CreateWidgetBlueprint fails if it exists),
then paste the helpers + the matching build_* function into
execute_tool_script and return build_*() from run().

Conventions used below
----------------------
* Every number is a Figma pixel value from the "Avatar Injury Prevention Program"
  file (see README/02_Figma_To_Unreal_Map.md for where each one comes from).
* font(kind, figma_px): Unreal font sizes are points at 96 DPI, so
  Unreal size = Figma px x 0.75 (Figma 20 px -> Unreal 15).
* Colours are Figma hex (sRGB) converted to Unreal linear colour by lc().
* Figma's Inter font is not in the project; the team's Avenir font is used:
  Inter Medium -> Avenir Medium, Inter Bold -> Avenir Heavy.
"""

import json

# Names of the MCP tool groups used below.
U = 'UMGToolSet.UMGToolSet.'                     # create widget blueprints / add widgets / compile
O = 'editor_toolset.toolsets.object.ObjectTools.'  # read / write any property
A = 'editor_toolset.toolsets.asset.AssetTools.'    # save assets


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def call(tool, args):
    """Run one MCP tool. execute_tool() is provided by the ProgrammaticToolset sandbox."""
    return execute_tool(tool, json.dumps(args))  # noqa: F821 (provided by the sandbox)


def getp(obj, names):
    return json.loads(call(O + 'get_properties', {'instance': obj, 'properties': names})['returnValue'])


def setp(obj, values):
    ok = call(O + 'set_properties', {'instance': obj, 'values': json.dumps(values)})['returnValue']
    if not ok:
        raise RuntimeError('set failed %s %s' % (obj, list(values.keys())))
    return ok


def s2l(c):
    """sRGB 0..255 -> linear 0..1 (the same maths as FLinearColor(FColor))."""
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lc(hex_color, a=1.0):
    h = hex_color.lstrip('#')
    return {'r': s2l(int(h[0:2], 16)), 'g': s2l(int(h[2:4], 16)), 'b': s2l(int(h[4:6], 16)), 'a': a}


def sc(hex_color, a=1.0):
    """FSlateColor with a specified colour."""
    return {'specifiedColor': lc(hex_color, a), 'colorUseRule': 'UseColor_Specified'}


TEX = '/Game/UserInterface/IHPC/Textures/'


def tex(name):
    return {'refPath': TEX + name + '.' + name}


FONTS = {
    'heavy': '/Game/UserInterface/Avenir-Font/Avenir/Avenir-Heavy_Font.Avenir-Heavy_Font',
    'medium': '/Game/UserInterface/Avenir-Font/Avenir/Avenir-Medium_Font.Avenir-Medium_Font',
}


def font(kind, figma_px):
    return {'fontObject': {'refPath': FONTS[kind]}, 'typefaceFontName': 'Default',
            'size': int(round(figma_px * 0.75)), 'letterSpacing': 0}


def brush_patch(b, draw, texname=None, size=None, color=('FFFFFF', 1.0), radii=(0, 0, 0, 0), outline=None):
    """Returns a copy of an existing FSlateBrush with new draw type / texture / colour / corner radii.
    radii order = top-left, top-right, bottom-right, bottom-left (Figma 'radius')."""
    b = dict(b)
    b['drawAs'] = draw                       # 'Image', 'RoundedBox' or 'NoDrawType'
    b['tintColor'] = sc(*color)
    if texname:
        b['resourceObject'] = tex(texname)
        b['imageType'] = 'FullColor'
        b['resourceName'] = 'None'
    else:
        # Plain colour: drop any engine picture inherited from the default style
        # (e.g. ProgressBar_Background.png), otherwise the colour is multiplied by it.
        b['resourceName'] = 'None'
        b['imageType'] = 'NoImage'
    if size:
        b['imageSize'] = {'x': size[0], 'y': size[1]}
    o = dict(b.get('outlineSettings', {}))
    o['cornerRadii'] = {'x': radii[0], 'y': radii[1], 'z': radii[2], 'w': radii[3]}
    o['roundingType'] = 'FixedRadius'
    o['bUseBrushTransparency'] = True
    o['color'] = sc(*(outline[0] if outline else ('000000', 0.0)))
    o['width'] = outline[1] if outline else 0
    b['outlineSettings'] = o
    return b


class BP:
    """Small wrapper around one Widget Blueprint being built."""

    def __init__(self, name, parent_class):
        folder = '/Game/UserInterface/IHPC/Widgets'
        self.pkg = folder + '/' + name
        self.ref = {'refPath': self.pkg + '.' + name}
        self.bp = call(U + 'CreateWidgetBlueprint', {'folderPath': folder, 'assetName': name,
                                                     'parentClass': {'refPath': parent_class}})['returnValue']
        self.w = {}

    def add(self, cls, name, parent=None, idx=-1):
        """Add a widget. cls = UMG class name ('Button') or a full class path."""
        cls_path = cls if cls.startswith('/') else '/Script/UMG.' + cls
        info = call(U + 'AddWidget', {'widgetBlueprint': self.bp, 'widgetClass': {'refPath': cls_path},
                                      'widgetDisplayName': name,
                                      'parentWidget': (self.w[parent]['widget'] if parent else None),
                                      'childIndex': idx})['returnValue']
        if not info or not info.get('widget'):
            raise RuntimeError('add failed ' + name)
        self.w[name] = info
        return info

    def W(self, n):
        return self.w[n]['widget']

    def S(self, n):
        return self.w[n]['slot']

    def canvas(self, n, x, y, w=0, h=0, anchors=(0, 0, 0, 0), align=(0, 0), auto=False, z=0):
        """Canvas Panel slot. With point anchors: x, y = position, w, h = size."""
        setp(self.S(n), {'LayoutData': {'offsets': {'left': x, 'top': y, 'right': w, 'bottom': h},
                                         'anchors': {'minimum': {'x': anchors[0], 'y': anchors[1]},
                                                     'maximum': {'x': anchors[2], 'y': anchors[3]}},
                                         'alignment': {'x': align[0], 'y': align[1]}},
                          'bAutoSize': auto, 'ZOrder': z})

    def pad(self, n, l=0, t=0, r=0, b=0, h=None, v=None):
        d = {'Padding': {'left': l, 'top': t, 'right': r, 'bottom': b}}
        if h:
            d['HorizontalAlignment'] = h
        if v:
            d['VerticalAlignment'] = v
        setp(self.S(n), d)

    def text(self, n, txt, kind, px, color=('FFFFFF', 1.0), just='Left'):
        setp(self.W(n), {'Text': txt, 'Font': font(kind, px), 'ColorAndOpacity': sc(*color), 'Justification': just})

    def button_style(self, n, normal, hovered, pressed):
        st = getp(self.W(n), ['WidgetStyle'])['WidgetStyle']
        st['normal'] = brush_patch(st['normal'], *normal[0], **normal[1])
        st['hovered'] = brush_patch(st['hovered'], *hovered[0], **hovered[1])
        st['pressed'] = brush_patch(st['pressed'], *pressed[0], **pressed[1])
        st['disabled'] = brush_patch(st['disabled'], 'NoDrawType')
        st['normalPadding'] = {'left': 0, 'top': 0, 'right': 0, 'bottom': 0}
        st['pressedPadding'] = {'left': 0, 'top': 0, 'right': 0, 'bottom': 0}
        # IsFocusable False: clicking a button must not steal keyboard focus from the 3D view.
        setp(self.W(n), {'WidgetStyle': st, 'IsFocusable': False, 'BackgroundColor': {'r': 1, 'g': 1, 'b': 1, 'a': 1}})

    def image(self, n, draw, texname=None, size=None, color=('FFFFFF', 1.0), radii=(0, 0, 0, 0), outline=None):
        b = getp(self.W(n), ['Brush'])['Brush']
        setp(self.W(n), {'Brush': brush_patch(b, draw, texname, size, color, radii, outline)})

    def border(self, n, draw, color=('FFFFFF', 1.0), radii=(0, 0, 0, 0), outline=None, padding=(0, 0, 0, 0), h=None, v=None):
        b = getp(self.W(n), ['Background'])['Background']
        d = {'Background': brush_patch(b, draw, None, None, color, radii, outline),
             'BrushColor': {'r': 1, 'g': 1, 'b': 1, 'a': 1},
             'Padding': {'left': padding[0], 'top': padding[1], 'right': padding[2], 'bottom': padding[3]}}
        if h:
            d['HorizontalAlignment'] = h
        if v:
            d['VerticalAlignment'] = v
        setp(self.W(n), d)

    def sizebox(self, n, w=None, h=None, maxh=None):
        d = {}
        if w is not None:
            d.update({'WidthOverride': w, 'bOverride_WidthOverride': True})
        if h is not None:
            d.update({'HeightOverride': h, 'bOverride_HeightOverride': True})
        if maxh is not None:
            d.update({'MaxDesiredHeight': maxh, 'bOverride_MaxDesiredHeight': True})
        setp(self.W(n), d)

    def vis(self, n, v):
        setp(self.W(n), {'Visibility': v})

    def finish(self, class_defaults=None):
        """Compile, set the Blueprint's class defaults (C++ UPROPERTYs), compile again, save."""
        ok = call(U + 'CompileWidgetBlueprint', {'widgetBlueprint': self.ref})['returnValue']
        if class_defaults:
            name = self.pkg.split('/')[-1]
            setp({'refPath': self.pkg + '.Default__' + name + '_C'}, class_defaults)
            ok = call(U + 'CompileWidgetBlueprint', {'widgetBlueprint': self.ref})['returnValue'] and ok
        saved = call(A + 'save_assets', {'asset_paths': [self.pkg]})['returnValue']
        return {'compiled': ok, 'saved': saved}


NONE = (('NoDrawType',), {})
HEADER_BTN = ((('RoundedBox',), {'color': ('D9D9D9', 0.20), 'radii': (11, 11, 11, 11)}),
              (('RoundedBox',), {'color': ('D9D9D9', 0.28), 'radii': (11, 11, 11, 11)}),
              (('RoundedBox',), {'color': ('D9D9D9', 0.34), 'radii': (11, 11, 11, 11)}))
ICON_BTN = (NONE,
            (('RoundedBox',), {'color': ('FFFFFF', 0.12), 'radii': (6, 6, 6, 6)}),
            (('RoundedBox',), {'color': ('FFFFFF', 0.20), 'radii': (6, 6, 6, 6)}))
WIDGETS = '/Game/UserInterface/IHPC/Widgets/'
LINEGRAPH = '/Script/MetaHumanTest.CPP_UW_IHPCLineGraph'


# ---------------------------------------------------------------------------
# 1. WBP_IHPC_ToggleSwitch  (Figma "Component 4", 38 x 20)
# ---------------------------------------------------------------------------

def build_toggle_switch():
    t = BP('WBP_IHPC_ToggleSwitch', '/Script/MetaHumanTest.CPP_UW_IHPCToggleSwitch')
    t.add('SizeBox', 'SwitchSize')
    t.sizebox('SwitchSize', 38, 20)
    t.add('CheckBox', 'SwitchCheckBox', 'SwitchSize')
    st = getp(t.W('SwitchCheckBox'), ['WidgetStyle'])['WidgetStyle']
    for key, texture in [('uncheckedImage', 'T_IHPC_Toggle_Off'), ('uncheckedHoveredImage', 'T_IHPC_Toggle_Off'),
                         ('uncheckedPressedImage', 'T_IHPC_Toggle_Off'), ('checkedImage', 'T_IHPC_Toggle_On'),
                         ('checkedHoveredImage', 'T_IHPC_Toggle_On'), ('checkedPressedImage', 'T_IHPC_Toggle_On')]:
        st[key] = brush_patch(st[key], 'Image', texture, (38, 20))
    st['uncheckedHoveredImage']['tintColor']['specifiedColor'] = {'r': 1.15, 'g': 1.15, 'b': 1.15, 'a': 1}  # hover = a bit brighter
    st['checkedHoveredImage']['tintColor']['specifiedColor'] = {'r': 1.1, 'g': 1.1, 'b': 1.1, 'a': 1}
    st['padding'] = {'left': 0, 'top': 0, 'right': 0, 'bottom': 0}
    for k in ['backgroundImage', 'backgroundHoveredImage', 'backgroundPressedImage']:
        st[k]['drawAs'] = 'NoDrawType'
    setp(t.W('SwitchCheckBox'), {'WidgetStyle': st, 'IsFocusable': False})
    return t.finish()


# ---------------------------------------------------------------------------
# 2. WBP_IHPC_NavTab  (Figma "Profile", "Progress", "Saved Videos", "History & Timeline", "Settings")
# ---------------------------------------------------------------------------

def build_nav_tab():
    t = BP('WBP_IHPC_NavTab', '/Script/MetaHumanTest.CPP_UW_IHPCNavTab')
    t.add('Button', 'TabButton')
    t.add('TextBlock', 'TabLabel', 'TabButton')
    t.button_style('TabButton', NONE, NONE, NONE)          # invisible button, the text is the visual
    t.text('TabLabel', 'Tab', 'medium', 20, just='Center')
    t.pad('TabLabel', 0, 0, 0, 0, 'HAlign_Center', 'VAlign_Center')
    return t.finish({'NormalFont': font('medium', 20),         # Figma Default: Inter Medium 20, white
                     'HighlightFont': font('heavy', 20),       # Figma Variant2: Inter Bold 24 (x1.2 scale), #B3CA7F
                     'HighlightScale': 1.2,
                     'NormalColor': sc('FFFFFF'), 'HighlightColor': sc('B3CA7F')})


# ---------------------------------------------------------------------------
# 3. WBP_IHPC_VideoCard  (one card from Figma "videos row", 240 x 95)
# ---------------------------------------------------------------------------

def build_video_card():
    c = BP('WBP_IHPC_VideoCard', '/Script/MetaHumanTest.CPP_UW_IHPCVideoCard')
    c.add('SizeBox', 'CardSize')
    c.sizebox('CardSize', 240, 95)
    c.add('Overlay', 'CardOverlay', 'CardSize')
    c.add('Image', 'CardBackground', 'CardOverlay')                     # text-free Figma card art
    c.image('CardBackground', 'Image', 'T_IHPC_VideoCard_BG', (240, 95))
    c.pad('CardBackground', h='HAlign_Fill', v='VAlign_Fill')
    c.add('CanvasPanel', 'CardContent', 'CardOverlay')
    c.pad('CardContent', h='HAlign_Fill', v='VAlign_Fill')
    c.vis('CardContent', 'SelfHitTestInvisible')
    c.add('TextBlock', 'TitleText', 'CardContent'); c.text('TitleText', 'Soleus Muscle (R)', 'heavy', 17); c.canvas('TitleText', 84, 21, 152, 24)
    c.add('TextBlock', 'DateText', 'CardContent');  c.text('DateText', 'Jan 4th, 2026', 'medium', 13);    c.canvas('DateText', 84, 47, 152, 18)
    c.add('TextBlock', 'TimeText', 'CardContent');  c.text('TimeText', '13:55 p.m.', 'medium', 13);       c.canvas('TimeText', 84, 63, 152, 18)
    for n in ['TitleText', 'DateText', 'TimeText']:
        setp(c.W(n), {'TextOverflowPolicy': 'Ellipsis', 'Visibility': 'HitTestInvisible'})
    c.add('Border', 'SeverityTick', 'CardContent')                     # white tick on the green-red bar
    c.border('SeverityTick', 'RoundedBox', ('FFFFFF', 1.0), (1.5, 1.5, 1.5, 1.5))
    c.canvas('SeverityTick', 0, 0, 3, 13)
    c.vis('SeverityTick', 'HitTestInvisible')
    c.add('Border', 'SelectionHighlight', 'CardContent')               # green outline when the card is picked
    c.border('SelectionHighlight', 'RoundedBox', ('FFFFFF', 0.0), (2, 2, 12, 12), (('B3CA7F', 1.0), 2))
    b = getp(c.W('SelectionHighlight'), ['Background'])['Background']
    b['outlineSettings']['bUseBrushTransparency'] = False              # keep the outline visible over a transparent fill
    setp(c.W('SelectionHighlight'), {'Background': b})
    c.canvas('SelectionHighlight', 0, 4, 240, 91)
    c.vis('SelectionHighlight', 'Hidden')
    c.add('Button', 'CardButton', 'CardOverlay')                       # invisible button over the whole card
    c.pad('CardButton', h='HAlign_Fill', v='VAlign_Fill')
    c.button_style('CardButton', NONE,
                   (('RoundedBox',), {'color': ('FFFFFF', 0.07), 'radii': (2, 2, 12, 12)}),
                   (('RoundedBox',), {'color': ('FFFFFF', 0.12), 'radii': (2, 2, 12, 12)}))
    return c.finish()


# ---------------------------------------------------------------------------
# 4. WBP_IHPC_VideosRow  (Figma "videos row", 858 x 160)
# ---------------------------------------------------------------------------

def build_videos_row():
    r = BP('WBP_IHPC_VideosRow', '/Script/MetaHumanTest.CPP_UW_IHPCVideosRow')
    r.add('CanvasPanel', 'RowCanvas')
    r.vis('RowCanvas', 'SelfHitTestInvisible')
    r.add('Image', 'ScrollTrack', 'RowCanvas')                         # Figma: rgba(255,255,255,0.05) 842x15
    r.image('ScrollTrack', 'RoundedBox', None, None, ('FFFFFF', 0.05), (7.5, 7.5, 7.5, 7.5))
    r.canvas('ScrollTrack', 3, 7, 842, 15)
    r.vis('ScrollTrack', 'HitTestInvisible')
    r.add('Slider', 'ScrollSlider', 'RowCanvas')                       # Figma thumb: rgba(153,191,222,0.51) 62x9
    r.canvas('ScrollSlider', 8, 10, 832, 9)
    st = getp(r.W('ScrollSlider'), ['WidgetStyle'])['WidgetStyle']
    for k in ['normalBarImage', 'hoveredBarImage', 'disabledBarImage']:
        st[k] = brush_patch(st[k], 'NoDrawType')
    st['normalThumbImage'] = brush_patch(st['normalThumbImage'], 'RoundedBox', None, (62, 9), ('99BFDE', 0.51), (4.5,) * 4)
    st['hoveredThumbImage'] = brush_patch(st['hoveredThumbImage'], 'RoundedBox', None, (62, 9), ('99BFDE', 0.80), (4.5,) * 4)
    st['disabledThumbImage'] = brush_patch(st['disabledThumbImage'], 'RoundedBox', None, (62, 9), ('99BFDE', 0.25), (4.5,) * 4)
    st['barThickness'] = 0
    setp(r.W('ScrollSlider'), {'WidgetStyle': st, 'IndentHandle': True, 'IsFocusable': False,
                               'MinValue': 0, 'MaxValue': 1, 'Value': 0})
    r.add('ScrollBox', 'CardScrollBox', 'RowCanvas')                   # cards are added here by C++
    r.canvas('CardScrollBox', 24, 41, 834, 119)
    setp(r.W('CardScrollBox'), {'Orientation': 'Orient_Horizontal', 'ScrollBarVisibility': 'Collapsed',
                                'ConsumeMouseWheel': 'Always', 'bAnimateWheelScrolling': True,
                                'AllowOverscroll': False, 'bIsFocusable': False})
    return r.finish({'CardClass': {'refPath': WIDGETS + 'WBP_IHPC_VideoCard.WBP_IHPC_VideoCard_C'}, 'CardSpacing': 23})


# ---------------------------------------------------------------------------
# 5. WBP_IHPC_GraphAccordion  (Figma "Component 3", 286 wide)
# ---------------------------------------------------------------------------

def build_graph_accordion():
    a = BP('WBP_IHPC_GraphAccordion', '/Script/MetaHumanTest.CPP_UW_IHPCGraphAccordion')
    a.add('SizeBox', 'AccordionSize'); a.sizebox('AccordionSize', w=286)
    a.add('VerticalBox', 'Sections', 'AccordionSize')

    def header(key, label, first):
        hb = 'Header_' + key
        a.add('Button', hb, 'Sections'); a.button_style(hb, *HEADER_BTN); a.pad(hb, 0, 0 if first else 13, 0, 0, 'HAlign_Fill')
        a.add('SizeBox', hb + '_Size', hb); a.sizebox(hb + '_Size', h=47); a.pad(hb + '_Size', h='HAlign_Fill', v='VAlign_Fill')
        a.add('Overlay', hb + '_Overlay', hb + '_Size')
        a.add('TextBlock', hb + '_Label', hb + '_Overlay'); a.text(hb + '_Label', label, 'heavy', 16)
        a.pad(hb + '_Label', 22, 0, 0, 0, 'HAlign_Left', 'VAlign_Center')
        a.add('Image', 'Chevron_' + key, hb + '_Overlay'); a.image('Chevron_' + key, 'Image', 'T_IHPC_Chevron_Down', (15, 9.5))
        a.pad('Chevron_' + key, 0, 0, 22, 0, 'HAlign_Right', 'VAlign_Center')
        a.vis(hb + '_Label', 'HitTestInvisible'); a.vis('Chevron_' + key, 'HitTestInvisible')

    # Show graphs (Figma Variant2 content, 560 tall, rgba(0,0,0,0.41))
    header('ShowGraphs', 'Show graphs', True)
    a.add('SizeBox', 'Content_ShowGraphs', 'Sections'); a.sizebox('Content_ShowGraphs', h=560); a.pad('Content_ShowGraphs', 0, 7, 0, 9, 'HAlign_Fill')
    a.add('Border', 'ShowGraphsPanel', 'Content_ShowGraphs'); a.border('ShowGraphsPanel', 'RoundedBox', ('000000', 0.41), (11,) * 4)
    a.add('CanvasPanel', 'ShowGraphsCanvas', 'ShowGraphsPanel'); a.vis('ShowGraphsCanvas', 'SelfHitTestInvisible')
    a.add('TextBlock', 'MovementGraphTitle', 'ShowGraphsCanvas'); a.text('MovementGraphTitle', 'Movement Graph', 'heavy', 16, just='Center'); a.canvas('MovementGraphTitle', 0, 20, 286, 24)
    a.add(LINEGRAPH, 'MovementGraph', 'ShowGraphsCanvas'); a.canvas('MovementGraph', 11, 45, 268, 142); setp(a.W('MovementGraph'), {'DemoSeed': 1})
    a.add('TextBlock', 'ActiveMusclesTitle', 'ShowGraphsCanvas'); a.text('ActiveMusclesTitle', 'Active Muscles', 'heavy', 16, just='Center'); a.canvas('ActiveMusclesTitle', 0, 208, 286, 24)
    a.add(LINEGRAPH, 'ActiveMusclesGraph', 'ShowGraphsCanvas'); a.canvas('ActiveMusclesGraph', 11, 233, 268, 142); setp(a.W('ActiveMusclesGraph'), {'DemoSeed': 8})
    for name, colour, y in [('Bones', '1D277E', 397), ('Nerves', '5D601E', 429), ('Muscles', '3C2718', 461), ('Tendons', '713D53', 493)]:
        a.add(WIDGETS + 'WBP_IHPC_ToggleSwitch.WBP_IHPC_ToggleSwitch_C', 'Toggle_' + name, 'ShowGraphsCanvas'); a.canvas('Toggle_' + name, 22, y, 38, 20)
        a.add('Image', 'Legend_' + name, 'ShowGraphsCanvas'); a.image('Legend_' + name, 'RoundedBox', None, (5, 18), (colour, 1.0), (2.5,) * 4); a.canvas('Legend_' + name, 70, y + 1, 5, 18)
        a.add('TextBlock', 'Label_' + name, 'ShowGraphsCanvas'); a.text('Label_' + name, name, 'heavy', 16); a.canvas('Label_' + name, 80, y - 2, 150, 24)
        a.vis('Label_' + name, 'HitTestInvisible'); a.vis('Legend_' + name, 'HitTestInvisible')
    a.add('Button', 'DownloadButton', 'ShowGraphsCanvas'); a.button_style('DownloadButton', *ICON_BTN); a.canvas('DownloadButton', 214, 523, 30, 30)
    setp(a.W('DownloadButton'), {'ToolTipText': 'Export the graph data to a CSV file'})
    a.add('Image', 'DownloadIcon', 'DownloadButton'); a.image('DownloadIcon', 'Image', 'T_IHPC_Download', (30, 30)); a.pad('DownloadIcon', h='HAlign_Fill', v='VAlign_Fill')
    a.add('Button', 'ZoomButton', 'ShowGraphsCanvas'); a.button_style('ZoomButton', *ICON_BTN); a.canvas('ZoomButton', 251, 528, 20, 19)
    setp(a.W('ZoomButton'), {'ToolTipText': 'Show a large Movement Graph'})
    a.add('Image', 'ZoomIcon', 'ZoomButton'); a.image('ZoomIcon', 'Image', 'T_IHPC_Zoom', (20, 19)); a.pad('ZoomIcon', h='HAlign_Fill', v='VAlign_Fill')

    # Active Muscles / Tagged Points (no Figma design for the open state -> simple scrolling list)
    for key, label, list_name in [('ActiveMuscles', 'Active Muscles', 'ActiveMusclesList'), ('TaggedPoints', 'Tagged Points', 'TaggedPointsList')]:
        header(key, label, False)
        cn = 'Content_' + key
        a.add('Border', cn, 'Sections'); a.border(cn, 'RoundedBox', ('000000', 0.41), (11,) * 4, None, (8, 8, 8, 8)); a.pad(cn, 0, 7, 0, 9, 'HAlign_Fill')
        a.add('SizeBox', key + '_ListSize', cn); a.sizebox(key + '_ListSize', maxh=260)
        a.add('ScrollBox', key + '_Scroll', key + '_ListSize'); setp(a.W(key + '_Scroll'), {'ScrollbarThickness': {'x': 4, 'y': 4}, 'bIsFocusable': False})
        a.add('VerticalBox', list_name, key + '_Scroll')

    return a.finish({'ChevronUpTexture': tex('T_IHPC_Chevron_Up'), 'ChevronDownTexture': tex('T_IHPC_Chevron_Down'),
                     'ListFont': font('medium', 15), 'StartOpenSection': 'None'})


# ---------------------------------------------------------------------------
# 6. WBP_IHPC_AnalysisPanel  (Figma frame "iPad Pro 12.9" - 5", panel 1217 x 798)
# ---------------------------------------------------------------------------

def build_analysis_panel():
    p = BP('WBP_IHPC_AnalysisPanel', '/Script/MetaHumanTest.CPP_UW_IHPCAnalysisPanel')
    p.add('SizeBox', 'PanelSize'); p.sizebox('PanelSize', 1217, 798)
    p.add('Border', 'PanelBackground', 'PanelSize'); p.border('PanelBackground', 'RoundedBox', ('000000', 0.62), (29,) * 4)
    p.add('CanvasPanel', 'PanelCanvas', 'PanelBackground'); p.vis('PanelCanvas', 'SelfHitTestInvisible')
    p.add('Border', 'ViewerFrame', 'PanelCanvas'); p.border('ViewerFrame', 'RoundedBox', ('000000', 0.29), (11,) * 4); p.canvas('ViewerFrame', 25, 21, 870, 559)
    p.add('Border', 'ZoomedGraphContainer', 'PanelCanvas'); p.border('ZoomedGraphContainer', 'RoundedBox', ('000000', 0.45), (11,) * 4, None, (16, 12, 16, 12)); p.canvas('ZoomedGraphContainer', 47, 49, 827, 508)
    p.add('VerticalBox', 'ZoomedGraphStack', 'ZoomedGraphContainer')
    p.add('TextBlock', 'ZoomedGraphTitle', 'ZoomedGraphStack'); p.text('ZoomedGraphTitle', 'Movement Graph', 'heavy', 22, just='Center'); p.pad('ZoomedGraphTitle', 0, 0, 0, 8, 'HAlign_Center')
    p.add(LINEGRAPH, 'ZoomedGraph', 'ZoomedGraphStack')
    setp(p.S('ZoomedGraph'), {'Size': {'value': 1, 'sizeRule': 'Fill'}, 'HorizontalAlignment': 'HAlign_Fill', 'VerticalAlignment': 'VAlign_Fill'})
    setp(p.W('ZoomedGraph'), {'bGenerateDemoDataIfEmpty': False, 'LineThickness': 2.5,
                              'PlotPadding': {'left': 34, 'top': 10, 'right': 10, 'bottom': 16},
                              'LabelFont': {'fontObject': {'refPath': '/Engine/EngineFonts/Roboto.Roboto'}, 'typefaceFontName': 'Regular', 'size': 11, 'letterSpacing': 0}})
    p.add('Button', 'InspectButton', 'PanelCanvas'); p.button_style('InspectButton', *ICON_BTN); p.canvas('InspectButton', 835, 519, 33, 33)
    setp(p.W('InspectButton'), {'ToolTipText': 'Inspect'})
    p.add('Image', 'InspectIcon', 'InspectButton'); p.image('InspectIcon', 'Image', 'T_IHPC_InspectCode', (33, 33)); p.pad('InspectIcon', h='HAlign_Fill', v='VAlign_Fill')
    p.add('Border', 'VideosArea', 'PanelCanvas'); p.border('VideosArea', 'RoundedBox', ('313131', 0.66), (11,) * 4); p.canvas('VideosArea', 25, 599, 870, 171)
    p.add(WIDGETS + 'WBP_IHPC_VideosRow.WBP_IHPC_VideosRow_C', 'VideosRow', 'PanelCanvas'); p.canvas('VideosRow', 31, 605, 858, 160)
    p.add(WIDGETS + 'WBP_IHPC_GraphAccordion.WBP_IHPC_GraphAccordion_C', 'GraphAccordion', 'PanelCanvas'); p.canvas('GraphAccordion', 910, 26, 286, 0, auto=True)
    return p.finish()


# ---------------------------------------------------------------------------
# 7. WBP_IHPC_HUD  (title bar + chevron + nav bar + analysis panel)
# ---------------------------------------------------------------------------

def build_hud():
    h = BP('WBP_IHPC_HUD', '/Script/MetaHumanTest.CPP_UW_IHPCHud')
    h.add('CanvasPanel', 'HudCanvas'); h.vis('HudCanvas', 'SelfHitTestInvisible')
    # Order = drawing order (later = on top): panel, chevron, nav bar, title bar.
    h.add(WIDGETS + 'WBP_IHPC_AnalysisPanel.WBP_IHPC_AnalysisPanel_C', 'AnalysisPanel', 'HudCanvas')
    h.canvas('AnalysisPanel', 0, 167, 1217, 798, (0.5, 0, 0.5, 0), (0.5, 0))
    h.add('SizeBox', 'ChevronGroup', 'HudCanvas'); h.sizebox('ChevronGroup', 83, 83)
    h.canvas('ChevronGroup', 0, 105, 83, 83, (0.5, 0, 0.5, 0), (0.5, 0.5)); h.vis('ChevronGroup', 'SelfHitTestInvisible')
    h.add('Overlay', 'ChevronOverlay', 'ChevronGroup'); h.vis('ChevronOverlay', 'SelfHitTestInvisible')
    h.add('Image', 'ChevronCircle', 'ChevronOverlay'); h.image('ChevronCircle', 'RoundedBox', None, (83, 83), ('FFFFFF', 1.0), (41.5,) * 4)
    h.pad('ChevronCircle', h='HAlign_Fill', v='VAlign_Fill'); h.vis('ChevronCircle', 'HitTestInvisible')
    h.add('Image', 'ChevronIcon', 'ChevronOverlay'); h.image('ChevronIcon', 'Image', 'T_IHPC_HeaderChevron_Down', (27, 12))
    h.pad('ChevronIcon', 0, 30, 0, 0, 'HAlign_Center', 'VAlign_Center'); h.vis('ChevronIcon', 'HitTestInvisible')
    h.add('Button', 'ChevronButton', 'ChevronOverlay'); h.button_style('ChevronButton', NONE, NONE, NONE)
    h.pad('ChevronButton', h='HAlign_Fill', v='VAlign_Fill'); setp(h.W('ChevronButton'), {'ToolTipText': 'Show / hide the menu'})
    h.add('VerticalBox', 'NavBar', 'HudCanvas'); h.canvas('NavBar', 0, 105, 0, 112, (0, 0, 1, 0))
    h.add('SizeBox', 'NavBarSize', 'NavBar'); h.sizebox('NavBarSize', None, 88); h.pad('NavBarSize', h='HAlign_Fill')
    h.add('Border', 'NavBarBackground', 'NavBarSize'); h.border('NavBarBackground', 'Image', ('274A65', 1.0), h='HAlign_Center', v='VAlign_Center')
    h.add('HorizontalBox', 'TabRow', 'NavBarBackground')
    tabs = ['Profile', 'Progress', 'SavedVideos', 'HistoryTimeline', 'Settings']
    for i, t in enumerate(tabs):
        h.add(WIDGETS + 'WBP_IHPC_NavTab.WBP_IHPC_NavTab_C', 'Tab_' + t, 'TabRow'); h.pad('Tab_' + t, v='VAlign_Center')
        if i < len(tabs) - 1:
            sep = 'TabSeparator_%d' % (i + 1)                      # Figma: 1 x 23, white 33%, 32 px gaps
            h.add('Image', sep, 'TabRow'); h.image(sep, 'Image', None, (1, 23), ('FFFFFF', 0.33)); h.pad(sep, 32, 0, 32, 0, None, 'VAlign_Center'); h.vis(sep, 'HitTestInvisible')
    h.add('Image', 'NavBarShadow', 'NavBar'); h.image('NavBarShadow', 'Image', 'T_IHPC_DropShadow', (4, 24)); h.pad('NavBarShadow', h='HAlign_Fill'); h.vis('NavBarShadow', 'HitTestInvisible')
    h.add('VerticalBox', 'TitleBar', 'HudCanvas'); h.canvas('TitleBar', 0, 0, 0, 129, (0, 0, 1, 0)); h.vis('TitleBar', 'SelfHitTestInvisible')
    h.add('SizeBox', 'TitleBarSize', 'TitleBar'); h.sizebox('TitleBarSize', None, 105); h.pad('TitleBarSize', h='HAlign_Fill')
    h.add('Overlay', 'TitleBarOverlay', 'TitleBarSize')
    h.add('Border', 'TitleBarBackground', 'TitleBarOverlay'); h.border('TitleBarBackground', 'Image', ('1D3C55', 1.0)); h.pad('TitleBarBackground', h='HAlign_Fill', v='VAlign_Fill')
    h.add('Image', 'TitleGlow', 'TitleBarOverlay'); h.image('TitleGlow', 'Image', 'T_IHPC_TitleGlow', (576, 54)); h.pad('TitleGlow', h='HAlign_Center', v='VAlign_Center'); h.vis('TitleGlow', 'HitTestInvisible')
    h.add('TextBlock', 'TitleText', 'TitleBarOverlay'); h.text('TitleText', 'AVATAR INJURY PREVENTION TECHNOLOGY', 'heavy', 24, just='Center')
    h.pad('TitleText', h='HAlign_Center', v='VAlign_Center'); h.vis('TitleText', 'HitTestInvisible')
    h.add('Image', 'TitleBarShadow', 'TitleBar'); h.image('TitleBarShadow', 'Image', 'T_IHPC_DropShadow', (4, 24)); h.pad('TitleBarShadow', h='HAlign_Fill'); h.vis('TitleBarShadow', 'HitTestInvisible')
    return h.finish({'ChevronClosedTexture': tex('T_IHPC_HeaderChevron_Down'),
                     'ChevronOpenTexture': tex('T_IHPC_HeaderChevron_Up_Blue'),
                     'AnalysisPanelTab': 'SavedVideos', 'bStartWithNavBarOpen': False, 'NavBarHeight': 88})


# ---------------------------------------------------------------------------
# 8. WBP_IHPC_Timeline  (Figma layer "ihpc ui (1)ee 1" on frame 1, 1048 x 102)   — added 2026-11-07
# ---------------------------------------------------------------------------

# name, texture, x, y, w, h, tooltip   (positions measured from the 3x Figma picture / 3)
TIMELINE_BUTTONS = [
    ('RecordButton', 'T_IHPC_TL_Record', 20.33, 28, 45.67, 45.67, 'Record a clip'),
    ('RestartButton', 'T_IHPC_TL_Restart', 75.67, 21.67, 58, 58, 'Restart'),
    ('PauseButton', 'T_IHPC_TL_Pause', 143.33, 18, 65, 65, 'Pause'),
    ('SlowDownButton', 'T_IHPC_TL_SlowDown', 217, 29, 46, 45.67, 'Slow down'),
    ('SpeedUpButton', 'T_IHPC_TL_SpeedUp', 798.67, 27, 46, 46, 'Speed up'),
    ('PlayButton', 'T_IHPC_TL_Play', 854, 18, 65, 65, 'Play'),
    ('FastForwardButton', 'T_IHPC_TL_FastForward', 927.33, 22.67, 56.33, 56, 'Fast-forward to the next marker'),
    ('BookmarkButton', 'T_IHPC_TL_Bookmark', 991.67, 28, 45.67, 45.67, 'Bookmark this moment'),
]


def tinted(b, texname, size, tint):
    """Image brush of a texture with a grey-scale tint (1.15 = brighter on hover, 0.8 = darker when pressed)."""
    b = brush_patch(b, 'Image', texname, size)
    b['tintColor'] = {'specifiedColor': {'r': tint, 'g': tint, 'b': tint, 'a': 1}, 'colorUseRule': 'UseColor_Specified'}
    return b


def build_timeline():
    t = BP('WBP_IHPC_Timeline', '/Script/MetaHumanTest.CPP_UW_IHPCTimeline')
    t.add('SizeBox', 'TimelineSize'); t.sizebox('TimelineSize', 1048, 102)
    t.add('CanvasPanel', 'TimelineCanvas', 'TimelineSize'); t.vis('TimelineCanvas', 'SelfHitTestInvisible')

    # Track: progress bar, fill = played #183C55, background = to play #7CAFD2, 513 x 10.67, fully rounded.
    t.add('ProgressBar', 'TrackProgress', 'TimelineCanvas'); t.canvas('TrackProgress', 274, 44, 513, 10.67)
    st = getp(t.W('TrackProgress'), ['WidgetStyle'])['WidgetStyle']
    st['backgroundImage'] = brush_patch(st['backgroundImage'], 'RoundedBox', None, None, ('7CAFD2', 1.0), (5.33,) * 4)
    st['fillImage'] = brush_patch(st['fillImage'], 'RoundedBox', None, None, ('183C55', 1.0), (5.33,) * 4)
    st['marqueeImage'] = brush_patch(st['marqueeImage'], 'NoDrawType')
    setp(t.W('TrackProgress'), {'WidgetStyle': st, 'BarFillType': 'LeftToRight', 'BarFillStyle': 'Scale',   # Scale = rounded end
                                'Percent': 0.545, 'FillColorAndOpacity': {'r': 1, 'g': 1, 'b': 1, 'a': 1},
                                'Visibility': 'HitTestInvisible'})

    # Invisible slider on top of the track for scrubbing (43 tall = knob height).
    t.add('Slider', 'ScrubSlider', 'TimelineCanvas'); t.canvas('ScrubSlider', 274, 28, 513, 43)
    ss = getp(t.W('ScrubSlider'), ['WidgetStyle'])['WidgetStyle']
    for k in ['normalBarImage', 'hoveredBarImage', 'disabledBarImage']:
        ss[k] = brush_patch(ss[k], 'NoDrawType')
    for k in ['normalThumbImage', 'hoveredThumbImage', 'disabledThumbImage']:
        ss[k] = brush_patch(ss[k], 'NoDrawType', None, (1, 43))
    ss['barThickness'] = 0
    setp(t.W('ScrubSlider'), {'WidgetStyle': ss, 'IndentHandle': False, 'IsFocusable': False,   # IndentHandle off: value = x / width
                              'MinValue': 0, 'MaxValue': 1, 'Value': 0.545,
                              'ToolTipText': 'Drag to move through the animation'})

    # Marker dots are created here by C++.
    t.add('CanvasPanel', 'MarkerLayer', 'TimelineCanvas'); t.canvas('MarkerLayer', 274, 44, 513, 10.67); t.vis('MarkerLayer', 'SelfHitTestInvisible')

    # Knob + speed text ("x1.5", Inter Medium 12 -> Avenir Medium 9), centred on the START of the track.
    t.add('Overlay', 'ThumbGroup', 'TimelineCanvas'); t.canvas('ThumbGroup', 274, 49.33, 44, 44, (0, 0, 0, 0), (0.5, 0.5)); t.vis('ThumbGroup', 'HitTestInvisible')
    t.add('Image', 'ThumbImage', 'ThumbGroup'); t.image('ThumbImage', 'Image', 'T_IHPC_TL_Thumb', (44, 44)); t.pad('ThumbImage', h='HAlign_Fill', v='VAlign_Fill')
    t.add('TextBlock', 'SpeedText', 'ThumbGroup'); t.text('SpeedText', 'x1.5', 'medium', 12, just='Center'); t.pad('SpeedText', h='HAlign_Center', v='VAlign_Center')

    # The eight glossy buttons.
    for name, texname, x, y, w, h, tip in TIMELINE_BUTTONS:
        t.add('Button', name, 'TimelineCanvas'); t.canvas(name, x, y, w, h)
        bs = getp(t.W(name), ['WidgetStyle'])['WidgetStyle']
        bs['normal'] = brush_patch(bs['normal'], 'Image', texname, (w, h))
        bs['hovered'] = tinted(bs['hovered'], texname, (w, h), 1.15)
        bs['pressed'] = tinted(bs['pressed'], texname, (w, h), 0.8)
        bs['disabled'] = tinted(bs['disabled'], texname, (w, h), 0.5)
        bs['normalPadding'] = {'left': 0, 'top': 0, 'right': 0, 'bottom': 0}
        bs['pressedPadding'] = {'left': 0, 'top': 0, 'right': 0, 'bottom': 0}
        setp(t.W(name), {'WidgetStyle': bs, 'IsFocusable': False, 'BackgroundColor': {'r': 1, 'g': 1, 'b': 1, 'a': 1}, 'ToolTipText': tip})

    # Record button content = the same picture, so C++ can tint it red while recording.
    t.add('Image', 'RecordIcon', 'RecordButton'); t.image('RecordIcon', 'Image', 'T_IHPC_TL_Record', (45.67, 45.67))
    t.pad('RecordIcon', h='HAlign_Fill', v='VAlign_Fill'); t.vis('RecordIcon', 'HitTestInvisible')
    # Red pulsing dot over the record button while recording.
    t.add('Image', 'RecordingIndicator', 'TimelineCanvas'); t.image('RecordingIndicator', 'RoundedBox', None, (12, 12), ('FF3B3B', 1.0), (6,) * 4)
    t.canvas('RecordingIndicator', 37.17, 44.83, 12, 12); t.vis('RecordingIndicator', 'Hidden')

    return t.finish({'MarkerTexture': tex('T_IHPC_TL_Marker'), 'TrackLength': 513, 'MarkerSize': 19, 'DesignerPreviewTime': 0.545})


def add_timeline_to_hud_and_retire_prototype():
    """Puts WBP_IHPC_Timeline into WBP_IHPC_HUD and stops BP_PlayerController creating WB_AmationTimeline."""
    hud = '/Game/UserInterface/IHPC/Widgets/WBP_IHPC_HUD.WBP_IHPC_HUD'
    info = call(U + 'AddWidget', {'widgetBlueprint': {'refPath': hud},
                                  'widgetClass': {'refPath': WIDGETS + 'WBP_IHPC_Timeline.WBP_IHPC_Timeline_C'},
                                  'widgetDisplayName': 'Timeline',
                                  'parentWidget': {'refPath': hud + ':WidgetTree.HudCanvas'},
                                  'childIndex': 0})['returnValue']        # index 0 = drawn behind the analysis panel
    # Bottom-centre, bar bottom 28 px above the screen bottom (Figma frame 1).
    setp(info['slot'], {'LayoutData': {'offsets': {'left': 0, 'top': -28, 'right': 1048, 'bottom': 102},
                                       'anchors': {'minimum': {'x': 0.5, 'y': 1}, 'maximum': {'x': 0.5, 'y': 1}},
                                       'alignment': {'x': 0.5, 'y': 1}}, 'bAutoSize': False, 'ZOrder': 0})
    call(U + 'CompileWidgetBlueprint', {'widgetBlueprint': {'refPath': hud}})
    pc = {'refPath': '/Game/Blueprints/BP_PlayerController.Default__BP_PlayerController_C'}
    setp(pc, {'TimelineWidgetClass': None})                               # old prototype no longer created
    return call(A + 'save_assets', {'asset_paths': ['/Game/UserInterface/IHPC/Widgets/WBP_IHPC_HUD',
                                                    '/Game/Blueprints/BP_PlayerController']})['returnValue']


def hook_hud_into_player_controller():
    """Later change (keeps the project's original organisation): the HUD is created by CPP_PlayerController
    (MainHUDWidgetClass, C++) instead of the Main Level Blueprint. Needs the C++ change built first."""
    pc = {'refPath': '/Game/Blueprints/BP_PlayerController.Default__BP_PlayerController_C'}
    setp(pc, {'MainHUDWidgetClass': {'refPath': WIDGETS + 'WBP_IHPC_HUD.WBP_IHPC_HUD_C'}})   # MainHUDZOrder stays 10
    B = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
    graph = '/Game/Main.Main:PersistentLevel.Main.EventGraph'
    # Unlink Begin Play first: delete_node alone left Begin Play's exec wire pointing at the deleted node
    # ("Statement tried to pass control flow to a node Create Widget that generates no code").
    call(B + 'break_pins', {'output_pin': {'direction': 'EGPD_Output', 'index_id': 1, 'node': {'refPath': graph + '.K2Node_Event_0'}},
                            'input_pin': {'direction': 'EGPD_Input', 'index_id': 0, 'node': {'refPath': graph + '.K2Node_CreateWidget_0'}}})
    for node in ['K2Node_CallFunction_0', 'K2Node_CreateWidget_0']:   # Add to Viewport + Create Widget (WBP_IHPC_HUD)
        call(B + 'delete_node', {'node': {'refPath': graph + '.' + node}})
    call(B + 'compile_blueprint', {'blueprint': {'refPath': '/Game/Main.Main:PersistentLevel.Main'}, 'warnings_as_errors': False})
    return call(A + 'save_assets', {'asset_paths': ['/Game/Blueprints/BP_PlayerController', '/Game/Main']})['returnValue']


# ---------------------------------------------------------------------------
# 10. WBP_IHPC_LayerSwitcher (Figma "ihpc ui rttd 2" + "Rectangle 24", frame 1, bottom right)
# ---------------------------------------------------------------------------
# Figma frame 1 (1366 x 1024): pill "Rectangle 24" 204 x 65 at (1114, 914); the 186 x 70 button picture
# at (1123, 913). Circle centres in the pill: x 43.45 / 102.33 / 161.2, y 32.69. The textures are 214 px
# crops of the 4.586x picture, so they are drawn at 214 / 4.586 = 46.66 px (circle = 46 px, like Figma).
LS_BUTTON = 46.66
LAYER_BUTTONS = [  # widget name, top-left x, y inside the pill, tooltip
    ('BodyLayer_Btn',     43.45 - LS_BUTTON / 2, 32.69 - LS_BUTTON / 2, 'Body'),
    ('MusclesLayer_Btn', 102.33 - LS_BUTTON / 2, 32.69 - LS_BUTTON / 2, 'Muscles'),
    ('SkeletonLayer_Btn', 161.2 - LS_BUTTON / 2, 32.69 - LS_BUTTON / 2, 'Skeleton'),
]
PLACEHOLDER_SWITCHER = '/Game/Widget/WB_AnatomyViewSwitcher.Default__WB_AnatomyViewSwitcher_C'


def build_layer_switcher():
    t = BP('WBP_IHPC_LayerSwitcher', '/Script/MetaHumanTest.CPP_UW_IHPCLayerSwitcher')
    # Full-screen root that lets clicks through everywhere except on the switcher itself.
    t.add('CanvasPanel', 'LayerRoot'); t.vis('LayerRoot', 'SelfHitTestInvisible')

    # The switcher: bottom-centre anchor, its centre 533 px right of the screen centre, bottom 45 px above the
    # screen bottom (Figma: pill centre x 1216 = 683 + 533, bottom 979 = 1024 - 45). Move it by moving this one.
    t.add('CanvasPanel', 'LayerSwitcher', 'LayerRoot'); t.vis('LayerSwitcher', 'SelfHitTestInvisible')
    t.canvas('LayerSwitcher', 533, -45, 204, 65, (0.5, 1, 0.5, 1), (0.5, 1))

    # "Rectangle 24": #1D3C55 at 26 %, fully rounded. Visible = clicks between the buttons don't reach the 3D view.
    t.add('Image', 'Pill', 'LayerSwitcher'); t.canvas('Pill', 0, 0, 204, 65)
    t.image('Pill', 'RoundedBox', None, (204, 65), ('1D3C55', 0.26), (32.5,) * 4)

    # The three buttons. Their pictures are set by C++ (selected / unselected), also in the designer.
    for name, x, y, tip in LAYER_BUTTONS:
        t.add('Button', name, 'LayerSwitcher'); t.canvas(name, x, y, LS_BUTTON, LS_BUTTON)
        setp(t.W(name), {'IsFocusable': False, 'ToolTipText': tip})

    # Orange badge on the skeleton button: white ring 16.8 px, centre (176.9, 16.55) in the pill. Added last = on top.
    t.add('Image', 'SkeletonBadge', 'LayerSwitcher'); t.canvas('SkeletonBadge', 176.9 - 8.4, 16.55 - 8.4, 16.8, 16.8)
    t.image('SkeletonBadge', 'Image', 'T_IHPC_LS_Badge', (16.8, 16.8)); t.vis('SkeletonBadge', 'HitTestInvisible')

    # The parent class (teammate's UCPP_UW_AnatomyViewSwitcher) needs these two by name. They stay hidden:
    # the new buttons drive the slider from C++, exactly like dragging the old placeholder slider.
    t.add('Button', 'AnatomyMetaHuman_Btn', 'LayerRoot'); t.vis('AnatomyMetaHuman_Btn', 'Collapsed')
    t.add('Slider', 'AnatomyViewSwitcher_Slider', 'LayerRoot'); t.vis('AnatomyViewSwitcher_Slider', 'Collapsed')
    setp(t.W('AnatomyViewSwitcher_Slider'), {'MinValue': 0, 'MaxValue': 1, 'Value': 1})

    # Hair / spawn settings copied from the placeholder so the parent code behaves the same.
    old = getp({'refPath': PLACEHOLDER_SWITCHER}, ['GroomStrandsAsset', 'GroomCardsAsset', 'PawnToSpawn'])
    defaults = dict(old)
    defaults.update({
        'BodySelectedTexture': tex('T_IHPC_LS_Body_On'), 'BodyUnselectedTexture': tex('T_IHPC_LS_Body_Off'),
        'MusclesSelectedTexture': tex('T_IHPC_LS_Muscles_On'), 'MusclesUnselectedTexture': tex('T_IHPC_LS_Muscles_Off'),
        'SkeletonSelectedTexture': tex('T_IHPC_LS_Skeleton_On'), 'SkeletonUnselectedTexture': tex('T_IHPC_LS_Skeleton_Off'),
        'ButtonSize': {'x': LS_BUTTON, 'y': LS_BUTTON},
    })
    return t.finish(defaults)


def hide_skeleton_badge():
    """Later change (team request): hide the orange badge on the Skeleton button. Class Default
    bShowSkeletonBadge = False (C++ then collapses SkeletonBadge); the designer copy is set Collapsed too.
    Note: AssetTools.save_assets refuses to work while Play-In-Editor is running."""
    pkg = WIDGETS + 'WBP_IHPC_LayerSwitcher'
    setp({'refPath': pkg + '.Default__WBP_IHPC_LayerSwitcher_C'}, {'bShowSkeletonBadge': False})
    setp({'refPath': pkg + '.WBP_IHPC_LayerSwitcher:WidgetTree.SkeletonBadge'}, {'Visibility': 'Collapsed'})
    call(U + 'CompileWidgetBlueprint', {'widgetBlueprint': {'refPath': pkg + '.WBP_IHPC_LayerSwitcher'}})
    return call(A + 'save_assets', {'asset_paths': [pkg]})['returnValue']


def use_layer_switcher_instead_of_placeholder():
    """BP_PlayerController creates the new switcher instead of WB_AnatomyViewSwitcher (same property, so the
    controller code is unchanged), and the timeline moves left of centre like Figma so the two sit side by side."""
    pc = {'refPath': '/Game/Blueprints/BP_PlayerController.Default__BP_PlayerController_C'}
    setp(pc, {'AnatomyViewSwitcherWidgetClass': {'refPath': WIDGETS + 'WBP_IHPC_LayerSwitcher.WBP_IHPC_LayerSwitcher_C'}})
    # Figma frame 1: timeline x 34..1082 -> centre 558 = 683 - 125. Its right end then stops 32 px before the pill.
    hud = '/Game/UserInterface/IHPC/Widgets/WBP_IHPC_HUD.WBP_IHPC_HUD'
    slot = getp({'refPath': hud + ':WidgetTree.Timeline'}, ['Slot'])['Slot']
    setp(slot, {'LayoutData': {'offsets': {'left': -125, 'top': -28, 'right': 1048, 'bottom': 102},
                               'anchors': {'minimum': {'x': 0.5, 'y': 1}, 'maximum': {'x': 0.5, 'y': 1}},
                               'alignment': {'x': 0.5, 'y': 1}}})
    call(U + 'CompileWidgetBlueprint', {'widgetBlueprint': {'refPath': hud}})
    return call(A + 'save_assets', {'asset_paths': ['/Game/Blueprints/BP_PlayerController',
                                                    '/Game/UserInterface/IHPC/Widgets/WBP_IHPC_HUD']})['returnValue']


# ---------------------------------------------------------------------------
# 11. Tab panels + close "X" in WBP_IHPC_HUD (step 4)
# ---------------------------------------------------------------------------
# Profile / Progress / History & Timeline / Settings get an empty panel with the look of Figma frame 5
# "Rectangle 26" (rgba(0,0,0,0.62), radius 29, 1217 x 798, 167 from the top, centred) - the same rectangle the
# analysis panel uses as its background. The close "X" is not in Figma: a 38 px round button in the HUD's
# colours (title-bar navy #1D3C55, hover = nav-bar #274A65, thin white rim) with the white rounded-stroke X,
# sitting on the panel's top-right rounded corner (centre 8.5 px in from both edges = on the corner curve).
TAB_PANELS = ['ProfilePanel', 'ProgressPanel', 'HistoryTimelinePanel', 'SettingsPanel']
CLOSE_SIZE = 38
CLOSE_BTN = ((('RoundedBox',), {'color': ('1D3C55', 1.0), 'radii': (CLOSE_SIZE / 2,) * 4, 'outline': (('FFFFFF', 0.35), 1.5)}),
             (('RoundedBox',), {'color': ('274A65', 1.0), 'radii': (CLOSE_SIZE / 2,) * 4, 'outline': (('FFFFFF', 0.55), 1.5)}),
             (('RoundedBox',), {'color': ('183C55', 1.0), 'radii': (CLOSE_SIZE / 2,) * 4, 'outline': (('FFFFFF', 0.35), 1.5)}))


def add_tab_panels_and_close_button():
    hud = WIDGETS + 'WBP_IHPC_HUD.WBP_IHPC_HUD'
    canvas = {'refPath': hud + ':WidgetTree.HudCanvas'}
    # Same slot as the analysis panel (top-centre, y 167, 1217 x 798).
    panel_layout = getp(getp({'refPath': hud + ':WidgetTree.AnalysisPanel'}, ['Slot'])['Slot'], ['LayoutData'])['LayoutData']

    def add(cls, name, parent, idx=-1):
        info = call(U + 'AddWidget', {'widgetBlueprint': {'refPath': hud}, 'widgetClass': {'refPath': '/Script/UMG.' + cls},
                                      'widgetDisplayName': name, 'parentWidget': parent, 'childIndex': idx})['returnValue']
        if not info or not info.get('widget'):
            raise RuntimeError('add failed ' + name)
        return info

    # HudCanvas order: Timeline, AnalysisPanel, [4 panels], [close X], ChevronGroup, NavBar, TitleBar.
    for i, name in enumerate(TAB_PANELS):
        info = add('Border', name, canvas, 2 + i)
        setp(info['slot'], {'LayoutData': panel_layout, 'bAutoSize': False, 'ZOrder': 0})
        b = getp(info['widget'], ['Background'])['Background']
        setp(info['widget'], {'Background': brush_patch(b, 'RoundedBox', None, None, ('000000', 0.62), (29,) * 4),
                              'BrushColor': {'r': 1, 'g': 1, 'b': 1, 'a': 1},
                              'Padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                              'Visibility': 'Collapsed'})
        add('CanvasPanel', name.replace('Panel', 'Content'), info['widget'])     # empty: the tab's content goes here

    info = add('Button', 'PanelCloseButton', canvas, 2 + len(TAB_PANELS))
    half_w = panel_layout['offsets']['right'] / 2.0                             # 608.5
    top = panel_layout['offsets']['top']                                       # 167
    setp(info['slot'], {'LayoutData': {'offsets': {'left': half_w - 8.5, 'top': top + 8.5, 'right': CLOSE_SIZE, 'bottom': CLOSE_SIZE},
                                       'anchors': {'minimum': {'x': 0.5, 'y': 0}, 'maximum': {'x': 0.5, 'y': 0}},
                                       'alignment': {'x': 0.5, 'y': 0.5}}, 'bAutoSize': False, 'ZOrder': 0})
    st = getp(info['widget'], ['WidgetStyle'])['WidgetStyle']
    for key, look in zip(['normal', 'hovered', 'pressed'], CLOSE_BTN):
        st[key] = brush_patch(st[key], *look[0], **look[1])
    st['disabled'] = brush_patch(st['disabled'], 'NoDrawType')
    st['normalPadding'] = {'left': 0, 'top': 0, 'right': 0, 'bottom': 0}
    st['pressedPadding'] = {'left': 0, 'top': 0, 'right': 0, 'bottom': 0}
    setp(info['widget'], {'WidgetStyle': st, 'IsFocusable': False, 'ToolTipText': 'Close',
                          'BackgroundColor': {'r': 1, 'g': 1, 'b': 1, 'a': 1}, 'Visibility': 'Collapsed'})
    icon = add('Image', 'PanelCloseIcon', info['widget'])
    b = getp(icon['widget'], ['Brush'])['Brush']
    setp(icon['widget'], {'Brush': brush_patch(b, 'Image', 'T_IHPC_Close', (16, 16)), 'Visibility': 'HitTestInvisible'})
    setp(icon['slot'], {'Padding': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
                        'HorizontalAlignment': 'HAlign_Center', 'VerticalAlignment': 'VAlign_Center'})

    ok = call(U + 'CompileWidgetBlueprint', {'widgetBlueprint': {'refPath': hud}})['returnValue']
    return {'compiled': ok, 'saved': call(A + 'save_assets', {'asset_paths': [WIDGETS + 'WBP_IHPC_HUD']})['returnValue']}


def run():
    """Build order matters: children before the widgets that contain them."""
    return {
        'ToggleSwitch': build_toggle_switch(),
        'NavTab': build_nav_tab(),
        'VideoCard': build_video_card(),
        'VideosRow': build_videos_row(),
        'GraphAccordion': build_graph_accordion(),
        'AnalysisPanel': build_analysis_panel(),
        'HUD': build_hud(),
        'Timeline': build_timeline(),
        'TimelineInHud': add_timeline_to_hud_and_retire_prototype(),
        'HudFromPlayerController': hook_hud_into_player_controller(),
        'LayerSwitcher': build_layer_switcher(),
        'LayerSwitcherInGame': use_layer_switcher_instead_of_placeholder(),
        'HideSkeletonBadge': hide_skeleton_badge(),
        'TabPanelsAndClose': add_tab_panels_and_close_button(),
    }
