# ============================================================
# Debug UI overlay
# Fullscreen renderer + optional debug windows
# Version: Stable_debug_safe (W/S/A/D + Q/E + F)
# ============================================================

style ui_text is default:
    font "DejaVuSans.ttf"
    size 18
    color "#EDEDED"

style ui_text_small is ui_text:
    size 14

style ui_mono_map_text is default:
    font "DejaVuSansMono.ttf"
    size 12
    color "#EDEDED"
    line_spacing 0
    kerning 0

style ui_overlay_frame is default:
    background Solid((10, 12, 16, 145))
    padding (8, 6)

style ui_button_text is default:
    font "DejaVuSans.ttf"
    size 14
    color "#F0F0F0"

style ui_button is default:
    background Solid((40, 46, 56, 215))
    hover_background Solid((68, 78, 94, 235))
    padding (8, 4)
    xmargin 0
    ymargin 0
    keyboard_focus False

screen debug_screen(app):
    tag game_debug
    modal True

    key "game_menu" action NullAction() capture True
    key "rollback" action NullAction() capture True
    key "rollforward" action NullAction() capture True
    key "dismiss" action NullAction() capture True
    key "focus_left" action NullAction() capture True
    key "focus_right" action NullAction() capture True
    key "focus_up" action NullAction() capture True
    key "focus_down" action NullAction() capture True
    key "button_select" action NullAction() capture True
    key "button_alternate" action NullAction() capture True
    key "K_ESCAPE" action NullAction() capture True

    key "w" action Function(app.do_forward) capture True
    key "K_w" action Function(app.do_forward) capture True

    if hasattr(app, "do_backward"):
        key "K_s" action [Function(renpy.notify, "K_s"), Function(app.do_backward)] capture True

    if hasattr(app, "do_strafe_left"):
        key "K_a" action [Function(renpy.notify, "K_a"), Function(app.do_strafe_left)] capture True

    if hasattr(app, "do_strafe_right"):
        key "K_d" action [Function(renpy.notify, "K_d"), Function(app.do_strafe_right)] capture True

    key "q" action Function(app.do_turn_left) capture True
    key "K_q" action Function(app.do_turn_left) capture True
    key "e" action Function(app.do_turn_right) capture True
    key "K_e" action Function(app.do_turn_right) capture True

    if hasattr(app, "do_interact"):
        key "f" action Function(app.do_interact) capture True
        key "K_f" action Function(app.do_interact) capture True

    if hasattr(app, "do_load_demo_hotkey"):
        key "1" action Function(app.do_load_demo_hotkey) capture True
        key "K_1" action Function(app.do_load_demo_hotkey) capture True

    if hasattr(app, "do_load_house_hotkey"):
        key "2" action Function(app.do_load_house_hotkey) capture True
        key "K_2" action Function(app.do_load_house_hotkey) capture True

    if hasattr(app, "do_load_maze_hotkey"):
        key "3" action Function(app.do_load_maze_hotkey) capture True
        key "K_3" action Function(app.do_load_maze_hotkey) capture True

    if hasattr(app, "do_load_maze_doors_hotkey"):
        key "4" action Function(app.do_load_maze_doors_hotkey) capture True
        key "K_4" action Function(app.do_load_maze_doors_hotkey) capture True

    if hasattr(app, "do_load_tunnel_hotkey"):
        key "5" action Function(app.do_load_tunnel_hotkey) capture True
        key "K_5" action Function(app.do_load_tunnel_hotkey) capture True

    if hasattr(app, "do_load_tunnel_doors_hotkey"):
        key "6" action Function(app.do_load_tunnel_doors_hotkey) capture True
        key "K_6" action Function(app.do_load_tunnel_doors_hotkey) capture True

    if hasattr(app, "do_look_up"):
        key "K_UP" action Function(app.do_look_up) capture True
    if hasattr(app, "do_look_down"):
        key "K_DOWN" action Function(app.do_look_down) capture True

    add app.view

    $ sw = config.screen_width
    $ sh = config.screen_height
    $ pad = max(12, int(sw * 0.010))
    $ gap = max(10, int(sw * 0.008))

    $ panel_w = max(215, int(sw * 0.115))
    $ panel_x = pad
    $ panel_y = pad

    $ tune_w = max(250, int(sw * 0.145))
    $ tune_x = panel_x + panel_w + gap
    $ tune_y = pad

    $ gen_w = max(300, int(sw * 0.165))
    $ gen_x = tune_x + tune_w + gap
    $ gen_y = pad

    $ map_w = max(290, int(sw * 0.155))
    $ map_h = max(170, int(sh * 0.22))
    $ map_x = sw - map_w - pad
    $ map_y = pad

    $ log_w = max(500, int(sw * 0.295))
    $ log_h = max(190, int(sh * 0.22))
    $ log_x = pad
    $ log_y = sh - log_h - pad

    $ status_w = log_w
    $ status_h = max(255, int(sh * 0.26))
    $ status_x = pad
    $ status_y = log_y - status_h - gap

    $ tests_w = max(760, int(sw * 0.49))
    $ tests_h = sh - (map_y + map_h + gap + pad)
    $ tests_x = sw - tests_w - pad
    $ tests_y = map_y + map_h + gap

    $ controls_y = sh - max(126, int(sh * 0.14))

    fixed:
        xfill True
        yfill True

        if getattr(app, "show_panel", True):
            frame:
                style "ui_overlay_frame"
                xpos panel_x
                ypos panel_y
                xsize panel_w
                vbox:
                    spacing 4
                    text "Panel" style "ui_text"
                    textbutton ("Controls: ON" if app.show_controls else "Controls: OFF") action Function(app.toggle_controls) style "ui_button" text_style "ui_button_text"
                    if hasattr(app, "toggle_status"):
                        textbutton ("Status: ON" if getattr(app, "show_status", True) else "Status: OFF") action Function(app.toggle_status) style "ui_button" text_style "ui_button_text"
                    textbutton ("Map: ON" if app.show_map else "Map: OFF") action Function(app.toggle_map) style "ui_button" text_style "ui_button_text"
                    textbutton ("Log: ON" if app.show_log else "Log: OFF") action Function(app.toggle_log) style "ui_button" text_style "ui_button_text"
                    textbutton ("Tests: ON" if app.show_tests else "Tests: OFF") action Function(app.toggle_tests) style "ui_button" text_style "ui_button_text"
                    if hasattr(app, "toggle_render_tune"):
                        textbutton ("Render: ON" if getattr(app, "show_render_tune", True) else "Render: OFF") action Function(app.toggle_render_tune) style "ui_button" text_style "ui_button_text"
                    if hasattr(app, "toggle_generator_ui"):
                        textbutton ("Generator UI: ON" if getattr(app, "show_generator_ui", False) else "Generator UI: OFF") action Function(app.toggle_generator_ui) style "ui_button" text_style "ui_button_text"
                    if hasattr(app, "toggle_panel"):
                        textbutton "Hide Panel" action Function(app.toggle_panel) style "ui_button" text_style "ui_button_text"
                    textbutton "Exit" action Return("exit_debug") style "ui_button" text_style "ui_button_text"
        else:
            frame:
                style "ui_overlay_frame"
                xpos panel_x
                ypos panel_y
                xsize max(110, int(panel_w * 0.62))
                vbox:
                    spacing 4
                    textbutton "Show Panel" action Function(app.toggle_panel) style "ui_button" text_style "ui_button_text"
                    textbutton "Exit" action Return("exit_debug") style "ui_button" text_style "ui_button_text"

        if getattr(app, "show_render_tune", True) and hasattr(app, "tune_fov_minus"):
            $ _rv = app._renderer_vals() if hasattr(app, "_renderer_vals") else None
            frame:
                style "ui_overlay_frame"
                xpos tune_x
                ypos tune_y
                xsize tune_w
                vbox:
                    spacing 4
                    text "Render Tune" style "ui_text"

                    hbox:
                        spacing 6
                        text ("FOV: %.1f" % (_rv["fov_deg"] if _rv else 0.0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_fov_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_fov_plus) style "ui_button" text_style "ui_button_text"

                    hbox:
                        spacing 6
                        text ("Proj: %.2f" % (_rv["proj_scale"] if _rv else 0.0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_proj_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_proj_plus) style "ui_button" text_style "ui_button_text"

                    hbox:
                        spacing 6
                        text ("Near: %.2f" % (_rv["near_clip_dist"] if _rv else 0.0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_near_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_near_plus) style "ui_button" text_style "ui_button_text"

                    hbox:
                        spacing 6
                        text ("WallH: %.2f" % (_rv["wall_height_world"] if _rv else 0.0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_wallh_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_wallh_plus) style "ui_button" text_style "ui_button_text"

                    hbox:
                        spacing 6
                        text ("CellM: %.2f" % (_rv["cell_size_world"] if _rv else 0.0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_cellm_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_cellm_plus) style "ui_button" text_style "ui_button_text"

                    hbox:
                        spacing 6
                        text ("Soft: %.2f" % (_rv["distance_soften"] if _rv else 0.0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_soft_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_soft_plus) style "ui_button" text_style "ui_button_text"

                    hbox:
                        spacing 6
                        text ("DoorH: %.2f" % (_rv["door_height_ratio"] if _rv else 0.0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_doorh_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_doorh_plus) style "ui_button" text_style "ui_button_text"

                    hbox:
                        spacing 6
                        text ("Frame: %.2f" % (_rv["door_frame_ratio"] if _rv else 0.0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_frame_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_frame_plus) style "ui_button" text_style "ui_button_text"

                    hbox:
                        spacing 6
                        text ("Inset: %.2f" % (_rv["door_inset_ratio"] if _rv else 0.0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_inset_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_inset_plus) style "ui_button" text_style "ui_button_text"

                    hbox:
                        spacing 6
                        text ("Ajar: %.1f" % (_rv["door_ajar_angle_deg"] if _rv else 0.0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_ajar_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_ajar_plus) style "ui_button" text_style "ui_button_text"

                    hbox:
                        spacing 6
                        text ("Cols: %d" % (_rv["columns_cap"] if _rv else 0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_cols_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_cols_plus) style "ui_button" text_style "ui_button_text"

                    if _rv:
                        text ("Render: %.2f ms   Avg20: %.2f ms" % (_rv["render_ms_last"], _rv["render_ms_avg"])) style "ui_text_small"

                    hbox:
                        spacing 6
                        textbutton "Preset Home" action Function(app.tune_render_home) style "ui_button" text_style "ui_button_text"
                        textbutton "Reset" action Function(app.tune_render_reset) style "ui_button" text_style "ui_button_text"

                    hbox:
                        spacing 6
                        if hasattr(app, "tune_render_save"):
                            textbutton "Save" action Function(app.tune_render_save) style "ui_button" text_style "ui_button_text"
                        if hasattr(app, "tune_render_clear_saved"):
                            textbutton "Clear Save" action Function(app.tune_render_clear_saved) style "ui_button" text_style "ui_button_text"

                    if hasattr(app, "has_saved_render_tune"):
                        text ("Saved profile: %s" % ("YES" if app.has_saved_render_tune() else "NO")) style "ui_text_small"

        if hasattr(app, "show_generator_ui") and app.show_generator_ui:
            frame:
                style "ui_overlay_frame"
                xpos gen_x
                ypos gen_y
                xsize gen_w
                ysize max(260, int(sh * 0.25))
                vbox:
                    spacing 4
                    text "Generator" style "ui_text"
                    text "Stable fixtures + exploration layouts" style "ui_text_small"
                    if hasattr(app, "do_gen_house_floor_mvp"):
                        textbutton "Generate house floor MVP [2]" action Function(app.do_gen_house_floor_mvp) style "ui_button" text_style "ui_button_text"
                    if hasattr(app, "do_gen_demo_room"):
                        textbutton "Load demo room [1]" action Function(app.do_gen_demo_room) style "ui_button" text_style "ui_button_text"
                    null height 4
                    text "New generated layouts" style "ui_text_small"
                    if hasattr(app, "do_gen_maze"):
                        textbutton "Generate maze [3]" action Function(app.do_gen_maze) style "ui_button" text_style "ui_button_text"
                    if hasattr(app, "do_gen_maze_doors"):
                        textbutton "Generate maze with doors [4]" action Function(app.do_gen_maze_doors) style "ui_button" text_style "ui_button_text"
                    if hasattr(app, "do_gen_tunnel"):
                        textbutton "Generate tunnel [5]" action Function(app.do_gen_tunnel) style "ui_button" text_style "ui_button_text"
                    if hasattr(app, "do_gen_tunnel_doors"):
                        textbutton "Generate tunnel with doors [6]" action Function(app.do_gen_tunnel_doors) style "ui_button" text_style "ui_button_text"
                    textbutton "Close" action Function(app.toggle_generator_ui) style "ui_button" text_style "ui_button_text"

        if getattr(app, "show_map", True):
            frame:
                style "ui_overlay_frame"
                xpos map_x
                ypos map_y
                xsize map_w
                ysize map_h
                vbox:
                    spacing 4
                    text "ASCII Map" style "ui_text"
                    viewport:
                        draggable True
                        mousewheel True
                        scrollbars "vertical"
                        ymaximum map_h - 40
                        text app.ascii_map() style "ui_mono_map_text" substitute False

        if getattr(app, "show_status", True):
            frame:
                style "ui_overlay_frame"
                xpos status_x
                ypos status_y
                xsize status_w
                ysize status_h
                vbox:
                    spacing 2
                    text "Status" style "ui_text"
                    text "Keys: W/S move, A/D strafe, Q/E turn, F interact" style "ui_text_small"
                    viewport:
                        draggable True
                        mousewheel True
                        scrollbars "vertical"
                        ymaximum status_h - 48
                        vbox:
                            spacing 2
                            for line in app.hud_lines():
                                text app.debug_markup_text(line) style "ui_text_small" substitute False

        if getattr(app, "show_log", True):
            frame:
                style "ui_overlay_frame"
                xpos log_x
                ypos log_y
                xsize log_w
                ysize log_h
                vbox:
                    spacing 3
                    hbox:
                        spacing 6
                        text "Log" style "ui_text"
                        text app.log_page_label() style "ui_text_small"
                    hbox:
                        spacing 6
                        textbutton "<<" action Function(app.log_page_oldest) sensitive app.can_log_page_older() style "ui_button" text_style "ui_button_text"
                        textbutton "<" action Function(app.log_page_older) sensitive app.can_log_page_older() style "ui_button" text_style "ui_button_text"
                        textbutton ">" action Function(app.log_page_newer) sensitive app.can_log_page_newer() style "ui_button" text_style "ui_button_text"
                        textbutton ">>" action Function(app.log_page_latest) sensitive app.can_log_page_newer() style "ui_button" text_style "ui_button_text"
                    vbox:
                        spacing 2
                        for line in app.log_rows_for_ui():
                            text line style "ui_text_small" substitute False

        if getattr(app, "show_tests", True):
            frame:
                style "ui_overlay_frame"
                xpos tests_x
                ypos tests_y
                xsize tests_w
                ysize tests_h
                vbox:
                    spacing 4
                    hbox:
                        spacing 10
                        text "Tests" style "ui_text"
                        textbutton "Run All" action Function(app.do_run_all_tests) style "ui_button" text_style "ui_button_text"
                        text ("Executed: %d" % len(app.test_results)) style "ui_text_small"
                    viewport:
                        draggable True
                        mousewheel True
                        scrollbars "vertical"
                        ymaximum tests_h - 46
                        vbox:
                            spacing 3
                            text "Available" style "ui_text_small"
                            for tname in app.available_tests():
                                textbutton ("Run: %s" % tname) action Function(app.do_run_test, tname) style "ui_button" text_style "ui_button_text"
                            null height 6
                            text "Executed results" style "ui_text_small"
                            if app.test_results:
                                for entry in reversed(app.test_results):
                                    $ name = entry[0]
                                    $ ok = entry[1]
                                    $ msg = entry[2] if len(entry) > 2 else ""
                                    $ row_text = app.debug_markup_text("%s | %s | %s" % (app.test_status_label(ok), name, msg))
                                    text row_text style "ui_text_small" substitute False layout "nobreak"
                            else:
                                text "No tests run yet." style "ui_text_small"

        if app.show_controls:
            frame:
                style "ui_overlay_frame"
                xalign 0.5
                ypos controls_y
                vbox:
                    spacing 3
                    hbox:
                        spacing 6
                        if hasattr(app, "do_look_up"):
                            textbutton "Look+" action Function(app.do_look_up) style "ui_button" text_style "ui_button_text"
                        if hasattr(app, "do_look_center"):
                            textbutton "Center" action Function(app.do_look_center) style "ui_button" text_style "ui_button_text"
                        if hasattr(app, "do_look_down"):
                            textbutton "Look-" action Function(app.do_look_down) style "ui_button" text_style "ui_button_text"
                    hbox:
                        spacing 6
                        textbutton "Turn L (Q)" action Function(app.do_turn_left) style "ui_button" text_style "ui_button_text"
                        if hasattr(app, "do_strafe_left"):
                            textbutton "Strafe L (A)" action Function(app.do_strafe_left) style "ui_button" text_style "ui_button_text"
                        textbutton "Fwd (W)" action Function(app.do_forward) style "ui_button" text_style "ui_button_text"
                        if hasattr(app, "do_strafe_right"):
                            textbutton "Strafe R (D)" action Function(app.do_strafe_right) style "ui_button" text_style "ui_button_text"
                        textbutton "Turn R (E)" action Function(app.do_turn_right) style "ui_button" text_style "ui_button_text"
                    hbox:
                        spacing 6
                        if hasattr(app, "do_backward"):
                            textbutton "Back (S)" action Function(app.do_backward) style "ui_button" text_style "ui_button_text"
                        if hasattr(app, "can_interact_door") and app.can_interact_door():
                            textbutton "Interact (F)" action Function(app.do_interact) style "ui_button" text_style "ui_button_text"
