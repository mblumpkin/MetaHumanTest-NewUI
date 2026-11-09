"""
build_final_festival_widgets.py
===============================

RECORD (and re-runnable script) of how the Widget Blueprints for the FINAL FESTIVAL redesign of the IHPC UI were
built (2026-11-08). Figma: "Avatar Injury Prevention Program", page "FINAL FESTIVAL" (node 498:2760).

The steps run inside the Unreal Editor through the Unreal MCP "ProgrammaticToolset" (execute_tool_script), the same
way as Tools/FigmaUI/build_widget_blueprints.py (the original UI). Each build_* function is pasted together with the
helpers below and returned from run(); execute_tool() is provided by the sandbox (only json / math / re / copy /
datetime / time can be imported there, so this file uses nothing else).

Order (each one uses the ones before it):
  build_side_tab, build_chat_panel, build_action_card, build_accordion_header, build_graph_card,
  build_graphs_panel, build_actions_panel, build_tagged_points_list, build_saved_videos_list,
  update_layer_switcher, build_side_bar, update_hud, update_player_controller

To rebuild a NEW Widget Blueprint, delete it first (CreateWidgetBlueprint fails if it exists). update_* functions edit
existing assets in place (WBP_IHPC_LayerSwitcher, WBP_IHPC_HUD, BP_PlayerController).

Conventions (same as the original record)
  * Numbers are Figma px (1366 x 1024 iPad frame) = Unreal Slate units. Positions were measured on the 1:1 frame
    screenshots (the Figma frames on this page are drawn rotated, so the layer coordinates are not screen coordinates).
  * font(kind, px): Unreal size = Figma px x 0.75. Avenir (already in the project) replaces Inter; the title uses the
    engine's Roboto Bold (Figma: Roboto ExtraBold, not shipped with the engine).
  * lc(): Figma sRGB hex -> Unreal linear colour.
"""

import json

U = 'UMGToolSet.UMGToolSet.'
O = 'editor_toolset.toolsets.object.ObjectTools.'
A = 'editor_toolset.toolsets.asset.AssetTools.'
CPP = '/Script/MetaHumanTest.'
WIDGETS = '/Game/UserInterface/IHPC/Widgets/'
TEX = '/Game/UserInterface/IHPC/Textures/'
LINEGRAPH = CPP + 'CPP_UW_IHPCLineGraph'


# ---------------------------------------------------------------------------
# Helpers (same as build_widget_blueprints.py, plus BP(..., create=False) to edit an existing Widget Blueprint)
# ---------------------------------------------------------------------------

def call(tool, args):
    return execute_tool(tool, json.dumps(args))  # noqa: F821 (provided by the sandbox)


def getp(obj, names):
    return json.loads(call(O + 'get_properties', {'instance': obj, 'properties': names})['returnValue'])


def setp(obj, values):
    ok = call(O + 'set_properties', {'instance': obj, 'values': json.dumps(values)})['returnValue']
    if not ok:
        raise RuntimeError('set failed %s %s' % (obj, list(values.keys())))
    return ok


def s2l(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lc(hex_color, a=1.0):
    h = hex_color.lstrip('#')
    return {'r': s2l(int(h[0:2], 16)), 'g': s2l(int(h[2:4], 16)), 'b': s2l(int(h[4:6], 16)), 'a': a}


def sc(hex_color, a=1.0):
    return {'specifiedColor': lc(hex_color, a), 'colorUseRule': 'UseColor_Specified'}


def tex(name):
    return {'refPath': TEX + name + '.' + name}


def wbp_class(name):
    return {'refPath': WIDGETS + name + '.' + name + '_C'}


FONTS = {
    'heavy': '/Game/UserInterface/Avenir-Font/Avenir/Avenir-Heavy_Font.Avenir-Heavy_Font',
    'medium': '/Game/UserInterface/Avenir-Font/Avenir/Avenir-Medium_Font.Avenir-Medium_Font',
    'roboto': '/Engine/EngineFonts/Roboto.Roboto',
}


def font(kind, figma_px, typeface='Default'):
    return {'fontObject': {'refPath': FONTS[kind]}, 'typefaceFontName': typeface,
            'size': int(round(figma_px * 0.75)), 'letterSpacing': 0}


def brush_patch(b, draw, texname=None, size=None, color=('FFFFFF', 1.0), radii=(0, 0, 0, 0), outline=None, tint=None):
    """Copy of an FSlateBrush with a new draw type / texture / colour / corner radii (top-left, top-right,
    bottom-right, bottom-left). tint = brightness multiplier for picture buttons (hover / pressed)."""
    b = dict(b)
    b['drawAs'] = draw
    if tint is not None:
        b['tintColor'] = {'specifiedColor': {'r': tint, 'g': tint, 'b': tint, 'a': 1.0}, 'colorUseRule': 'UseColor_Specified'}
    else:
        b['tintColor'] = sc(*color)
    if texname:
        b['resourceObject'] = tex(texname)
        b['imageType'] = 'FullColor'
        b['resourceName'] = 'None'
    else:
        # Plain colour: drop any engine picture inherited from the default style, otherwise it multiplies the colour.
        b['resourceName'] = 'None'
        b['imageType'] = 'NoImage'
    if size:
        b['imageSize'] = {'x': size[0], 'y': size[1]}
    o = dict(b.get('outlineSettings', {}))
    o['cornerRadii'] = {'x': radii[0], 'y': radii[1], 'z': radii[2], 'w': radii[3]}
    o['roundingType'] = 'FixedRadius'
    o['bUseBrushTransparency'] = outline is None
    o['color'] = sc(*(outline[0] if outline else ('000000', 0.0)))
    o['width'] = outline[1] if outline else 0
    b['outlineSettings'] = o
    return b


class BP:
    """One Widget Blueprint being built (create=True) or edited (create=False)."""

    def __init__(self, name, parent_class=None, create=True, folder=WIDGETS):
        self.name = name
        self.pkg = folder + name
        self.ref = {'refPath': self.pkg + '.' + name}
        self.w = {}
        if create:
            self.bp = call(U + 'CreateWidgetBlueprint', {'folderPath': folder.rstrip('/'), 'assetName': name,
                                                         'parentClass': {'refPath': parent_class}})['returnValue']
        else:
            self.bp = self.ref
            self.reload()

    def reload(self):
        """Reads the existing widget tree into self.w (name -> {'widget':..., 'slot':...})."""
        tree = call(U + 'GetWidgets', {'widgetBlueprint': self.ref})['returnValue']
        self.w = {}
        for info in tree['widgets']:          # (the sandbox's dicts do not support .get(key, default))
            if isinstance(info['widget'], dict):
                self.w[str(info['widgetName'])] = info

    def add(self, cls, name, parent=None, idx=-1):
        cls_path = cls if cls.startswith('/') else '/Script/UMG.' + cls
        info = call(U + 'AddWidget', {'widgetBlueprint': self.bp, 'widgetClass': {'refPath': cls_path},
                                      'widgetDisplayName': name,
                                      'parentWidget': (self.w[parent]['widget'] if parent else None),
                                      'childIndex': idx})['returnValue']
        if not info or not info.get('widget'):
            raise RuntimeError('add failed ' + name)
        self.w[name] = info
        return info

    def remove(self, name):
        if name in self.w:
            ok = call(U + 'RemoveWidget', {'widgetBlueprint': self.bp, 'widget': self.w[name]['widget']})['returnValue']
            self.reload()
            return ok
        return False

    def W(self, n):
        return self.w[n]['widget']

    def S(self, n):
        return self.w[n]['slot']

    def canvas(self, n, x, y, w=0, h=0, anchors=(0, 0, 0, 0), align=(0, 0), auto=False, z=0):
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

    def text(self, n, txt, kind, px, color=('FFFFFF', 1.0), just='Left', typeface='Default'):
        setp(self.W(n), {'Text': txt, 'Font': font(kind, px, typeface), 'ColorAndOpacity': sc(*color), 'Justification': just})

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

    def picture_button(self, n, texname, size):
        """Button drawn as a picture: normal, hovered (x1.15 brighter), pressed (x0.8)."""
        self.button_style(n, (('Image', texname, size), {'tint': 1.0}),
                          (('Image', texname, size), {'tint': 1.15}),
                          (('Image', texname, size), {'tint': 0.8}))

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

    def sizebox(self, n, w=None, h=None):
        d = {}
        if w is not None:
            d.update({'WidthOverride': w, 'bOverride_WidthOverride': True})
        if h is not None:
            d.update({'HeightOverride': h, 'bOverride_HeightOverride': True})
        setp(self.W(n), d)

    def vis(self, n, v):
        setp(self.W(n), {'Visibility': v})

    def finish(self, class_defaults=None):
        """Compile, set the Blueprint's class defaults (C++ UPROPERTYs), compile again, save."""
        ok = call(U + 'CompileWidgetBlueprint', {'widgetBlueprint': self.ref})['returnValue']
        if class_defaults:
            setp({'refPath': self.pkg + '.Default__' + self.name + '_C'}, class_defaults)
            ok = call(U + 'CompileWidgetBlueprint', {'widgetBlueprint': self.ref})['returnValue'] and ok
        saved = call(A + 'save_assets', {'asset_paths': [self.pkg]})['returnValue']
        return {'asset': self.name, 'compiled': ok, 'saved': saved}


NONE = (('NoDrawType',), {})
HEADER_BTN = ((('RoundedBox',), {'color': ('D9D9D9', 0.20), 'radii': (11, 11, 11, 11)}),
              (('RoundedBox',), {'color': ('D9D9D9', 0.28), 'radii': (11, 11, 11, 11)}),
              (('RoundedBox',), {'color': ('D9D9D9', 0.34), 'radii': (11, 11, 11, 11)}))
ICON_BTN = (NONE,
            (('RoundedBox',), {'color': ('FFFFFF', 0.12), 'radii': (5, 5, 5, 5)}),
            (('RoundedBox',), {'color': ('FFFFFF', 0.20), 'radii': (5, 5, 5, 5)}))


def no_scrollbar(bp, n, vertical=True):
    """Figma draws no scroll bars: scroll with the mouse wheel / drag; the next item peeking in shows there is more."""
    setp(bp.W(n), {'ScrollBarVisibility': 'Collapsed', 'Orientation': 'Orient_Vertical' if vertical else 'Orient_Horizontal',
                   'AllowOverscroll': False})


# ---------------------------------------------------------------------------
# 1. WBP_IHPC_SideTab - one round tab button in the side bar (55 x 55; picture set by C++ from the Icons)
# ---------------------------------------------------------------------------

def build_side_tab():
    t = BP('WBP_IHPC_SideTab', CPP + 'CPP_UW_IHPCSideTab')
    t.add('SizeBox', 'TabSize')
    t.sizebox('TabSize', 55, 55)
    t.add('Button', 'TabButton', 'TabSize')
    t.button_style('TabButton', NONE, NONE, NONE)       # C++ (RefreshVisuals) gives it the normal / active picture
    return t.finish({'ButtonSize': {'x': 55, 'y': 55}})


# ---------------------------------------------------------------------------
# 2. WBP_IHPC_ChatPanel - Figma component "BOT", Variant2 (window 279 x 286 next to the avatar)
# ---------------------------------------------------------------------------

def build_chat_panel():
    c = BP('WBP_IHPC_ChatPanel', CPP + 'CPP_UW_IHPCChatPanel')
    c.add('SizeBox', 'ChatSize')
    c.sizebox('ChatSize', 279, 286)
    c.add('Border', 'ChatBackground', 'ChatSize')                          # rgba(12,39,61,0.72), radius 18
    c.border('ChatBackground', 'RoundedBox', ('0C273D', 0.72), (18, 18, 18, 18))
    c.add('CanvasPanel', 'ChatCanvas', 'ChatBackground')
    c.add('ScrollBox', 'MessageList', 'ChatCanvas')                        # bubbles (C++); first bubble at (11, 18)
    c.canvas('MessageList', 11, 18, 257, 213)
    setp(c.W('MessageList'), {'ScrollBarThickness': {'x': 3, 'y': 3}})
    c.add('Border', 'InputBackground', 'ChatCanvas')                       # white 13 %, fully round, 212 x 35
    c.border('InputBackground', 'RoundedBox', ('FFFFFF', 0.13), (17.5, 17.5, 17.5, 17.5), padding=(15, 0, 10, 0),
             h='HAlign_Fill', v='VAlign_Center')
    c.canvas('InputBackground', 11, 241, 212, 35)
    c.add('EditableTextBox', 'MessageInput', 'InputBackground')
    st = getp(c.W('MessageInput'), ['WidgetStyle'])['WidgetStyle']
    for k in list(st.keys()):
        if k.startswith('backgroundImage'):
            st[k] = brush_patch(st[k], 'NoDrawType')
    st['padding'] = {'left': 0, 'top': 4, 'right': 0, 'bottom': 4}
    st['foregroundColor'] = sc('FFFFFF')
    if 'textStyle' in st:
        st['textStyle']['font'] = font('medium', 15)
        st['textStyle']['colorAndOpacity'] = sc('FFFFFF')
    else:
        st['font'] = font('medium', 15)
    setp(c.W('MessageInput'), {'WidgetStyle': st, 'HintText': 'Type here', 'ClearKeyboardFocusOnCommit': False})
    c.add('Button', 'SendButton', 'ChatCanvas')                            # round frosted button + send arrow
    c.canvas('SendButton', 229, 239, 40, 40)
    c.picture_button('SendButton', 'T_IHPC_SB_Button', (40, 40))
    c.add('Image', 'SendIcon', 'SendButton')
    c.image('SendIcon', 'Image', 'T_IHPC_ChatSend', (18, 20))
    c.pad('SendIcon', 1, 0, 0, 0, 'HAlign_Center', 'VAlign_Center')
    c.vis('SendIcon', 'HitTestInvisible')
    setp(c.W('SendButton'), {'ToolTipText': 'Send'})
    return c.finish({'BubbleFont': font('medium', 15)})


# ---------------------------------------------------------------------------
# 3. WBP_IHPC_ActionCard - Figma frame 19 card (269 x 147, radius 14)
# ---------------------------------------------------------------------------

def build_action_card():
    a = BP('WBP_IHPC_ActionCard', CPP + 'CPP_UW_IHPCActionCard')
    a.add('SizeBox', 'CardSize')
    a.sizebox('CardSize', 269, 147)
    a.add('Overlay', 'CardOverlay', 'CardSize')
    a.add('Image', 'CardPicture', 'CardOverlay')                           # mannequin + gradient + rounded corners
    a.image('CardPicture', 'Image', 'T_IHPC_ActionCard', (269, 147))
    a.pad('CardPicture', h='HAlign_Fill', v='VAlign_Fill')
    a.add('TextBlock', 'CardLabel', 'CardOverlay')                         # Avenir Heavy 20 px, (16, ~8)
    a.text('CardLabel', 'Idle', 'heavy', 20)
    a.pad('CardLabel', 16, 6, 16, 0, 'HAlign_Left', 'VAlign_Top')
    a.vis('CardLabel', 'HitTestInvisible')
    a.add('Border', 'SelectionHighlight', 'CardOverlay')                   # green outline = action playing
    a.border('SelectionHighlight', 'RoundedBox', ('FFFFFF', 0.0), (14, 14, 14, 14), (('B3CA7F', 1.0), 2.5))
    a.pad('SelectionHighlight', h='HAlign_Fill', v='VAlign_Fill')
    a.vis('SelectionHighlight', 'Hidden')
    a.add('Button', 'CardButton', 'CardOverlay')                           # invisible button over the card
    a.pad('CardButton', h='HAlign_Fill', v='VAlign_Fill')
    a.button_style('CardButton', NONE,
                   (('RoundedBox',), {'color': ('FFFFFF', 0.08), 'radii': (14, 14, 14, 14)}),
                   (('RoundedBox',), {'color': ('FFFFFF', 0.14), 'radii': (14, 14, 14, 14)}))
    return a.finish()


# ---------------------------------------------------------------------------
# 4. WBP_IHPC_AccordionHeader - Graphs panel header (270 x 47)
# ---------------------------------------------------------------------------

def build_accordion_header():
    h = BP('WBP_IHPC_AccordionHeader', CPP + 'CPP_UW_IHPCAccordionHeader')
    h.add('SizeBox', 'HeaderSize')
    h.sizebox('HeaderSize', 270, 47)
    h.add('Button', 'HeaderButton', 'HeaderSize')
    h.button_style('HeaderButton', *HEADER_BTN)                            # rgba(217,217,217,0.2), radius 11
    h.add('Overlay', 'HeaderContent', 'HeaderButton')
    h.pad('HeaderContent', h='HAlign_Fill', v='VAlign_Fill')
    h.vis('HeaderContent', 'HitTestInvisible')
    h.add('TextBlock', 'HeaderLabel', 'HeaderContent')                     # Inter Bold 16 -> Avenir Heavy 12 pt
    h.text('HeaderLabel', 'Arms', 'heavy', 16)
    h.pad('HeaderLabel', 21, 0, 40, 0, 'HAlign_Left', 'VAlign_Center')
    h.add('Image', 'HeaderChevron', 'HeaderContent')                       # 14.36 x 9.16 at x 236
    h.image('HeaderChevron', 'Image', 'T_IHPC_AccChevron_Down', (14.36, 9.16))
    h.pad('HeaderChevron', 0, 0, 19.6, 0, 'HAlign_Right', 'VAlign_Center')
    return h.finish({'ChevronOpenTexture': tex('T_IHPC_AccChevron_Up'),
                     'ChevronClosedTexture': tex('T_IHPC_AccChevron_Down')})


# ---------------------------------------------------------------------------
# 5. WBP_IHPC_GraphCard - Figma frames 21 / 22 open section (270 x 447)
# ---------------------------------------------------------------------------

def build_graph_card():
    g = BP('WBP_IHPC_GraphCard', CPP + 'CPP_UW_IHPCGraphCard')
    g.add('SizeBox', 'CardSize')
    g.sizebox('CardSize', 270, 447)
    g.add('Border', 'CardBackground', 'CardSize')                          # rgba(0,0,0,0.41), radius 11
    g.border('CardBackground', 'RoundedBox', ('000000', 0.41), (11, 11, 11, 11))
    g.add('CanvasPanel', 'CardCanvas', 'CardBackground')

    g.add('TextBlock', 'MovementGraphTitle', 'CardCanvas')
    g.text('MovementGraphTitle', 'Movement Graph', 'heavy', 16, just='Center')
    g.canvas('MovementGraphTitle', 0, 20, 270, 24)
    g.add(LINEGRAPH, 'MovementGraph', 'CardCanvas')
    g.canvas('MovementGraph', 6, 44, 258, 106)
    setp(g.W('MovementGraph'), {'DemoSeed': 1})

    g.add('TextBlock', 'ActiveMusclesTitle', 'CardCanvas')
    g.text('ActiveMusclesTitle', 'Active Muscles', 'heavy', 16, just='Center')
    g.canvas('ActiveMusclesTitle', 0, 166, 270, 24)
    g.add(LINEGRAPH, 'ActiveMusclesGraph', 'CardCanvas')
    g.canvas('ActiveMusclesGraph', 6, 190, 258, 106)
    setp(g.W('ActiveMusclesGraph'), {'DemoSeed': 8})

    # Switches + legend bars + labels (Figma: centres at y 325 / 350 / 376 / 402).
    rows = [('Bones', '1D277E', 325), ('Nerves', '5D601E', 350), ('Muscles', '3C2718', 376), ('Tendons', '713D53', 402)]
    for name, colour, cy in rows:
        g.add(WIDGETS + 'WBP_IHPC_ToggleSwitch.WBP_IHPC_ToggleSwitch_C', 'Toggle_' + name, 'CardCanvas')
        g.canvas('Toggle_' + name, 20, cy - 10, 38, 20)
        g.add('Image', 'Legend_' + name, 'CardCanvas')
        g.image('Legend_' + name, 'RoundedBox', None, (5, 14), (colour, 1.0), (2.5, 2.5, 2.5, 2.5))
        g.canvas('Legend_' + name, 66, cy - 7, 5, 14)
        g.vis('Legend_' + name, 'HitTestInvisible')
        g.add('TextBlock', 'Label_' + name, 'CardCanvas')
        g.text('Label_' + name, name, 'heavy', 16)
        g.canvas('Label_' + name, 76, cy - 12, 120, 24)
        g.vis('Label_' + name, 'HitTestInvisible')

    # Bookmark / download / zoom (Figma: bottom right, y ~421).
    for btn, icon, texname, rect, size in [
            ('BookmarkButton', 'BookmarkIcon', 'T_IHPC_GraphBookmark', (181, 417, 25, 24), (15, 16)),
            ('DownloadButton', 'DownloadIcon', 'T_IHPC_Download', (206, 415, 28, 28), (26, 26)),
            ('ZoomButton', 'ZoomIcon', 'T_IHPC_GraphZoom', (234, 417, 25, 24), (19, 16))]:
        g.add('Button', btn, 'CardCanvas')
        g.canvas(btn, *rect)
        g.button_style(btn, *ICON_BTN)
        g.add('Image', icon, btn)
        g.image(icon, 'Image', texname, size)
        g.pad(icon, h='HAlign_Center', v='VAlign_Center')
        g.vis(icon, 'HitTestInvisible')
    setp(g.W('BookmarkButton'), {'ToolTipText': 'Bookmark this moment'})
    setp(g.W('DownloadButton'), {'ToolTipText': 'Download the graphs (CSV)'})
    setp(g.W('ZoomButton'), {'ToolTipText': 'Show a large graph'})
    return g.finish()


# ---------------------------------------------------------------------------
# 6. WBP_IHPC_GraphsPanel - Graphs side panel content (body-region accordion, 270 wide)
# ---------------------------------------------------------------------------

def build_graphs_panel():
    p = BP('WBP_IHPC_GraphsPanel', CPP + 'CPP_UW_IHPCGraphsPanel')
    p.add('SizeBox', 'PanelSize')
    p.sizebox('PanelSize', 270)
    p.add('ScrollBox', 'RegionScroll', 'PanelSize')
    no_scrollbar(p, 'RegionScroll')
    p.add('VerticalBox', 'RegionList', 'RegionScroll')                     # headers + card are put here by C++
    p.add(WIDGETS + 'WBP_IHPC_GraphCard.WBP_IHPC_GraphCard_C', 'GraphCard', 'RegionList')
    return p.finish({'HeaderClass': wbp_class('WBP_IHPC_AccordionHeader')})


# ---------------------------------------------------------------------------
# 7. WBP_IHPC_ActionsPanel - Action side panel content (column of cards, 270 wide)
# ---------------------------------------------------------------------------

def build_actions_panel():
    s = BP('WBP_IHPC_ActionsPanel', CPP + 'CPP_UW_IHPCActionsPanel')
    s.add('SizeBox', 'PanelSize')
    s.sizebox('PanelSize', 270)
    s.add('ScrollBox', 'CardList', 'PanelSize')                            # cards are added here by C++
    no_scrollbar(s, 'CardList')
    return s.finish({'CardClass': wbp_class('WBP_IHPC_ActionCard'), 'DefaultCardPicture': tex('T_IHPC_ActionCard'),
                     'CardSpacing': 25})


# ---------------------------------------------------------------------------
# 8. WBP_IHPC_TaggedPointsList - Timeline side panel content (270 wide)
# ---------------------------------------------------------------------------

def build_tagged_points_list():
    l = BP('WBP_IHPC_TaggedPointsList', CPP + 'CPP_UW_IHPCTaggedPointsList')
    l.add('SizeBox', 'ListSize')
    l.sizebox('ListSize', 270)
    l.add('Overlay', 'ListOverlay', 'ListSize')
    l.add('ScrollBox', 'PointsScroll', 'ListOverlay')
    l.pad('PointsScroll', h='HAlign_Fill', v='VAlign_Fill')
    no_scrollbar(l, 'PointsScroll')
    l.add('VerticalBox', 'PointsList', 'PointsScroll')                     # rows are added here by C++
    l.add('TextBlock', 'EmptyText', 'ListOverlay')
    l.text('EmptyText', 'No tagged points yet. Bookmark a moment on the timeline or on a graph.', 'medium', 15,
           ('FFFFFF', 0.6))
    setp(l.W('EmptyText'), {'AutoWrapText': True})
    l.pad('EmptyText', 0, 8, 0, 0, 'HAlign_Fill', 'VAlign_Top')
    return l.finish({'ListFont': font('medium', 15), 'RowSpacing': 6})


# ---------------------------------------------------------------------------
# 9. WBP_IHPC_SavedVideosList - Saved Videos side panel content (vertical list of video cards)
# ---------------------------------------------------------------------------

def build_saved_videos_list():
    v = BP('WBP_IHPC_SavedVideosList', CPP + 'CPP_UW_IHPCVideosRow')
    v.add('SizeBox', 'ListSize')
    v.sizebox('ListSize', 270)
    v.add('ScrollBox', 'CardScrollBox', 'ListSize')                        # same C++ as the old videos row, vertical
    no_scrollbar(v, 'CardScrollBox')
    return v.finish({'CardClass': wbp_class('WBP_IHPC_VideoCard'), 'CardSpacing': 16})


# ---------------------------------------------------------------------------
# 10. WBP_IHPC_LayerSwitcher (existing) - stacked vertically for the side bar, new Icons pictures
# ---------------------------------------------------------------------------

def update_layer_switcher():
    s = BP('WBP_IHPC_LayerSwitcher', create=False)
    s.remove('Pill')                                                       # the side bar's pill is behind it now
    # Figma (frame 16): buttons 55 px, tops 8 / 67 / 127 inside the pill -> 0 / 59 / 119 here.
    s.canvas('LayerSwitcher', 0, 0, 55, 174)
    s.canvas('BodyLayer_Btn', 0, 0, 55, 55)
    s.canvas('MusclesLayer_Btn', 0, 59, 55, 55)
    s.canvas('SkeletonLayer_Btn', 0, 119, 55, 55)
    s.canvas('SkeletonBadge', 38, 118, 16.8, 16.8)                         # still hidden (bShowSkeletonBadge off)
    return s.finish({'BodySelectedTexture': tex('T_IHPC_SB_Skin_Active'), 'BodyUnselectedTexture': tex('T_IHPC_SB_Skin'),
                     'MusclesSelectedTexture': tex('T_IHPC_SB_Muscles_Active'), 'MusclesUnselectedTexture': tex('T_IHPC_SB_Muscles'),
                     'SkeletonSelectedTexture': tex('T_IHPC_SB_Skeleton_Active'), 'SkeletonUnselectedTexture': tex('T_IHPC_SB_Skeleton'),
                     'ButtonSize': {'x': 55, 'y': 55}})


# ---------------------------------------------------------------------------
# 11. WBP_IHPC_SideBar - the side bar (Figma frames 15 / 16)
# ---------------------------------------------------------------------------

SIDE_TABS = [
    # widget name          TabId             label              icon
    ('Tab_Actions',        'Actions',        'Action',          'T_IHPC_SB_Activity'),
    ('Tab_PoseEstimation', 'PoseEstimation', 'Pose Estimation', 'T_IHPC_SB_PoseEstimation'),
    ('Tab_Graphs',         'Graphs',         'Graphs',          'T_IHPC_SB_Graph'),
    ('Tab_Timeline',       'Timeline',       'Timeline',        'T_IHPC_SB_Timeline'),
    ('Tab_SavedVideos',    'SavedVideos',    'Saved Videos',    'T_IHPC_SB_SavedVideos'),
    ('Tab_Settings',       'Settings',       'Settings',        'T_IHPC_SB_Settings'),
]


def build_side_bar():
    b = BP('WBP_IHPC_SideBar', CPP + 'CPP_UW_IHPCSideBar')
    b.add('CanvasPanel', 'SideBarRoot')
    b.vis('SideBarRoot', 'SelfHitTestInvisible')
    b.add('Button', 'BotButton', 'SideBarRoot')                            # 69 x 69 avatar (picture set by C++)
    b.canvas('BotButton', 0, 0, 69, 69)
    b.button_style('BotButton', NONE, NONE, NONE)
    b.add(WIDGETS + 'WBP_IHPC_ChatPanel.WBP_IHPC_ChatPanel_C', 'ChatPanel', 'SideBarRoot')
    b.canvas('ChatPanel', 80, 0, 279, 286)                                 # Figma: window 80 px right of the avatar
    b.add('Border', 'Pill', 'SideBarRoot')                                 # "Rectangle 24": rgba(12,39,61,0.59)
    b.border('Pill', 'RoundedBox', ('0C273D', 0.59), (34.5, 34.5, 34.5, 34.5), padding=(0, 8, 0, 7))
    b.canvas('Pill', 0, 78, 69, 0, auto=True)                              # 78 = 212 - 134 (pill top - avatar top)
    b.add('VerticalBox', 'PillStack', 'Pill')
    b.add(WIDGETS + 'WBP_IHPC_LayerSwitcher.WBP_IHPC_LayerSwitcher_C', 'LayerSwitcher', 'PillStack')
    b.pad('LayerSwitcher', 7, 0, 7, 0, 'HAlign_Center')
    b.add('VerticalBox', 'ExtraTabs', 'PillStack')
    b.pad('ExtraTabs', 0, 0, 0, 0, 'HAlign_Center')

    def sep(name, top):
        b.add('Image', name, 'ExtraTabs')                                  # "Vector 7": 16 px white line, 0.5 px
        b.image(name, 'RoundedBox', None, (16, 1), ('FFFFFF', 0.5))
        b.pad(name, 0, top, 0, 0, 'HAlign_Center')
        b.vis(name, 'HitTestInvisible')

    def tab(name, top):
        b.add(WIDGETS + 'WBP_IHPC_SideTab.WBP_IHPC_SideTab_C', name, 'ExtraTabs')
        b.pad(name, 0, top, 0, 0, 'HAlign_Center')

    # Figma (frame 16), tops inside the pill: sep 193, Action 205 | sep 271, Pose 283, Graphs 340 |
    # sep 406, Timeline 418, Saved Videos 478, Settings 538.
    sep('Separator_1', 11)
    tab('Tab_Actions', 11)
    sep('Separator_2', 11)
    tab('Tab_PoseEstimation', 11)
    tab('Tab_Graphs', 2)
    sep('Separator_3', 11)
    tab('Tab_Timeline', 11)
    tab('Tab_SavedVideos', 5)
    tab('Tab_Settings', 5)
    for name, tab_id, label, icon in SIDE_TABS:
        setp(b.W(name), {'TabId': tab_id, 'Label': label, 'NormalTexture': tex(icon), 'ActiveTexture': tex(icon + '_Active')})

    b.add('Button', 'ExpandButton', 'PillStack')                           # "Group 30": 57 px circle + chevron
    b.pad('ExpandButton', 0, 27, 0, 0, 'HAlign_Center')                    # C++ sets 27 (collapsed) / 32 (expanded)
    b.add('Image', 'ExpandIcon', 'ExpandButton')
    b.image('ExpandIcon', 'Image', 'T_IHPC_SB_Chevron_Down', (29, 13))
    # A Button is as big as its content (not its picture): pad the 29 x 13 chevron out to the 57 x 57 circle.
    b.pad('ExpandIcon', 14, 22, 14, 22, 'HAlign_Center', 'VAlign_Center')
    b.vis('ExpandIcon', 'HitTestInvisible')
    return b.finish({'BotTexture': tex('T_IHPC_Bot'), 'ExpandButtonTexture': tex('T_IHPC_SB_Button'),
                     'ExpandTexture': tex('T_IHPC_SB_Chevron_Down'), 'CollapseTexture': tex('T_IHPC_SB_Chevron_Up')})


# ---------------------------------------------------------------------------
# 12. WBP_IHPC_HUD (existing) - nav bar / chevron / big panels out; side bar, side panel, reset view in
# ---------------------------------------------------------------------------

def update_hud():
    h = BP('WBP_IHPC_HUD', create=False)
    removed = {}
    for old in ['AnalysisPanel', 'ProfilePanel', 'ProgressPanel', 'HistoryTimelinePanel', 'SettingsPanel',
                'PanelCloseButton', 'ChevronGroup', 'NavBar']:
        removed[old] = h.remove(old)

    # Title bar: 112 tall (Figma "Rectangle 13"), glow 576 x 112, title Roboto (ExtraBold in Figma) 24 px.
    h.sizebox('TitleBarSize', h=112)
    h.image('TitleGlow', 'Image', 'T_IHPC_TitleGlow', (576, 112))
    setp(h.W('TitleText'), {'Font': font('roboto', 24, 'Bold')})

    # Timeline: centred at the bottom, 26 px above the edge (Figma frame 15: bar 159..1207, bottom at 998).
    h.canvas('Timeline', 0, -26, 1048, 102, anchors=(0.5, 1, 0.5, 1), align=(0.5, 1))

    # z-order = child order: Timeline, ZoomedGraphPanel, ResetViewButton, SidePanel, SideBar, TitleBar (last = on top).
    # --- Zoomed graph (graph card zoom icon): free area of the screen, Figma "Rectangle 26" style
    h.add('Border', 'ZoomedGraphPanel', 'HudCanvas', 1)
    h.border('ZoomedGraphPanel', 'RoundedBox', ('000000', 0.62), (29, 29, 29, 29))
    h.canvas('ZoomedGraphPanel', 0, -20, 760, 440, anchors=(0.5, 0.5, 0.5, 0.5), align=(0.5, 0.5))
    h.add('CanvasPanel', 'ZoomedGraphCanvas', 'ZoomedGraphPanel')
    h.add('TextBlock', 'ZoomedGraphTitle', 'ZoomedGraphCanvas')
    h.text('ZoomedGraphTitle', 'Movement Graph', 'heavy', 20, just='Center')
    h.canvas('ZoomedGraphTitle', 0, 18, 760, 30)
    h.add(LINEGRAPH, 'ZoomedGraph', 'ZoomedGraphCanvas')
    h.canvas('ZoomedGraph', 24, 58, 712, 362)
    h.add('Button', 'ZoomedGraphCloseButton', 'ZoomedGraphCanvas')
    h.canvas('ZoomedGraphCloseButton', 704, 12, 42, 42)
    h.button_style('ZoomedGraphCloseButton', NONE, NONE, NONE)             # picture set by C++ (RoundButtonTexture)
    h.add('Image', 'ZoomedGraphCloseX', 'ZoomedGraphCloseButton')
    h.image('ZoomedGraphCloseX', 'Image', 'T_IHPC_PanelClose_X', (12.59, 13))
    h.pad('ZoomedGraphCloseX', h='HAlign_Center', v='VAlign_Center')
    h.vis('ZoomedGraphCloseX', 'HitTestInvisible')
    h.vis('ZoomedGraphPanel', 'Collapsed')

    # --- Reset view (Figma frame 17): 68 px navy circle + round arrow, 24 px from the right, top 134
    h.add('Button', 'ResetViewButton', 'HudCanvas', 2)
    h.canvas('ResetViewButton', -24, 134, 68, 68, anchors=(1, 0, 1, 0), align=(1, 0))
    h.button_style('ResetViewButton', NONE, NONE, NONE)                    # rounded colour set by C++ (ResetViewColor)
    h.add('Image', 'ResetViewIcon', 'ResetViewButton')
    h.image('ResetViewIcon', 'Image', 'T_IHPC_ResetView', (30.18, 32.63))
    h.pad('ResetViewIcon', h='HAlign_Center', v='VAlign_Center')
    h.vis('ResetViewIcon', 'HitTestInvisible')

    # --- Side panel (Figma "Rectangle 31": #0E2334, x 0..332, below the title bar; shadow on its right edge)
    h.add('CanvasPanel', 'SidePanel', 'HudCanvas', 3)
    h.canvas('SidePanel', 0, 112, 360, 0, anchors=(0, 0, 0, 1))
    h.add('Image', 'SidePanelShadow', 'SidePanel')
    h.image('SidePanelShadow', 'Image', 'T_IHPC_DropShadowRight', (24, 4))
    h.canvas('SidePanelShadow', 332, 0, 24, 0, anchors=(0, 0, 0, 1))
    h.vis('SidePanelShadow', 'HitTestInvisible')
    h.add('Border', 'SidePanelBackground', 'SidePanel')
    h.border('SidePanelBackground', 'Image', ('0E2334', 1.0))
    h.canvas('SidePanelBackground', 0, 0, 332, 0, anchors=(0, 0, 0, 1))
    h.add('Image', 'PanelIcon', 'SidePanel')                               # the tab's frosted icon, 43 px
    h.image('PanelIcon', 'Image', 'T_IHPC_SB_Activity', (43, 43))
    h.canvas('PanelIcon', 32, 22, 43, 43)
    h.vis('PanelIcon', 'HitTestInvisible')
    h.add('TextBlock', 'PanelTitle', 'SidePanel')                          # Avenir Heavy 24 px, white
    h.text('PanelTitle', 'Action', 'heavy', 24)
    h.canvas('PanelTitle', 82, 26, 170, 34)
    h.vis('PanelTitle', 'HitTestInvisible')
    h.add('Button', 'PanelCloseButton', 'SidePanel')                       # round frosted button + X, 42 px
    h.canvas('PanelCloseButton', 264, 22, 42, 42)
    h.button_style('PanelCloseButton', NONE, NONE, NONE)                   # picture set by C++ (RoundButtonTexture)
    h.add('Image', 'PanelCloseX', 'PanelCloseButton')
    h.image('PanelCloseX', 'Image', 'T_IHPC_PanelClose_X', (12.59, 13))
    h.pad('PanelCloseX', h='HAlign_Center', v='VAlign_Center')
    h.vis('PanelCloseX', 'HitTestInvisible')
    # Contents: column x 34, width 270, from y 92 (Figma: first card / header at 204) to the bottom.
    for name, cls in [('ActionsPanel', WIDGETS + 'WBP_IHPC_ActionsPanel.WBP_IHPC_ActionsPanel_C'),
                      ('PoseEstimationContent', 'CanvasPanel'),
                      ('GraphsPanel', WIDGETS + 'WBP_IHPC_GraphsPanel.WBP_IHPC_GraphsPanel_C'),
                      ('TaggedPointsList', WIDGETS + 'WBP_IHPC_TaggedPointsList.WBP_IHPC_TaggedPointsList_C'),
                      ('SavedVideosList', WIDGETS + 'WBP_IHPC_SavedVideosList.WBP_IHPC_SavedVideosList_C'),
                      ('SettingsContent', 'CanvasPanel')]:
        h.add(cls, name, 'SidePanel')
        h.canvas(name, 34, 92, 270, 0, anchors=(0, 0, 0, 1))
        h.vis(name, 'Collapsed')
    h.vis('SidePanel', 'Collapsed')

    # --- Side bar (Figma frame 15: avatar at (24, 134))
    h.add(WIDGETS + 'WBP_IHPC_SideBar.WBP_IHPC_SideBar_C', 'SideBar', 'HudCanvas', 4)
    h.canvas('SideBar', 24, 134, 0, 0, auto=True)

    result = h.finish({'RoundButtonTexture': tex('T_IHPC_SB_Button')})
    result['removed'] = removed
    return result


# ---------------------------------------------------------------------------
# 13. BP_PlayerController - the layer switcher lives in the side bar now: do not create a second one
# ---------------------------------------------------------------------------

def update_player_controller():
    cdo = {'refPath': '/Game/Blueprints/BP_PlayerController.Default__BP_PlayerController_C'}
    setp(cdo, {'AnatomyViewSwitcherWidgetClass': None})
    bp = {'refPath': '/Game/Blueprints/BP_PlayerController.BP_PlayerController'}
    saved = call(A + 'save_assets', {'asset_paths': ['/Game/Blueprints/BP_PlayerController']})['returnValue']
    return {'AnatomyViewSwitcherWidgetClass': getp(cdo, ['AnatomyViewSwitcherWidgetClass']), 'saved': saved, 'bp': bp}


# ---------------------------------------------------------------------------
# 14. Fixes found in Play-In-Editor (2026-11-09)
# ---------------------------------------------------------------------------

def fit_panel_title():
    """WBP_IHPC_HUD: the panel title shrinks to fit (ScaleBox, down only) so a long name such as "Pose Estimation"
    stops short of the close button (title 82..258, X at 264). Short names keep Figma's 24 px."""
    h = BP('WBP_IHPC_HUD', create=False)
    for old in ['PanelTitle', 'PanelTitleFit']:                            # re-runnable
        h.remove(old)
    h.add('ScaleBox', 'PanelTitleFit', 'SidePanel', 3)                     # same place in the list as the old title
    h.canvas('PanelTitleFit', 82, 26, 176, 34)
    setp(h.W('PanelTitleFit'), {'Stretch': 'ScaleToFit', 'StretchDirection': 'DownOnly'})
    h.vis('PanelTitleFit', 'HitTestInvisible')
    h.add('TextBlock', 'PanelTitle', 'PanelTitleFit')                      # C++ BindWidget: same name and type
    h.text('PanelTitle', 'Action', 'heavy', 24)
    setp(h.S('PanelTitle'), {'HorizontalAlignment': 'HAlign_Left', 'VerticalAlignment': 'VAlign_Center'})  # (no Padding)
    return h.finish()


def move_speed_slider():
    """BP_SpeedSlider (the project's walk / jog / run slider, not in Figma): it sat at the bottom left, where the
    expanded side bar now is (it showed through the pill). Moved to the middle of the right edge, the one free area in
    every FINAL FESTIVAL frame (the reset-view button is top right, the timeline bottom centre)."""
    s = BP('BP_SpeedSlider', create=False, folder='/Game/Blueprints/')
    s.canvas('SpeedSliderCanvas', -49, 0, 44, 344, anchors=(1, 0.5, 1, 0.5), align=(1, 0.5))
    return s.finish()
