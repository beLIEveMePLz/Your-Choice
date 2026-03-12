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

screen debug_screen(app):
    tag game_debug
    modal True

    # Hard capture keyboard controls
    key "w" action Function(app.do_forward) capture True
    key "K_w" action Function(app.do_forward) capture True

    if hasattr(app, "do_backward"):
        key "s" action Function(app.do_backward) capture True
        key "K_s" action Function(app.do_backward) capture True

    if hasattr(app, "do_strafe_left"):
        key "a" action Function(app.do_strafe_left) capture True
        key "K_a" action Function(app.do_strafe_left) capture True

    if hasattr(app, "do_strafe_right"):
        key "d" action Function(app.do_strafe_right) capture True
        key "K_d" action Function(app.do_strafe_right) capture True

    key "q" action Function(app.do_turn_left) capture True
    key "K_q" action Function(app.do_turn_left) capture True
    key "e" action Function(app.do_turn_right) capture True
    key "K_e" action Function(app.do_turn_right) capture True

    if hasattr(app, "do_interact"):
        key "f" action Function(app.do_interact) capture True
        key "K_f" action Function(app.do_interact) capture True

    if hasattr(app, "do_look_up"):
        key "K_UP" action Function(app.do_look_up) capture True
    if hasattr(app, "do_look_down"):
        key "K_DOWN" action Function(app.do_look_down) capture True

    add app.view

    fixed:
        xfill True
        yfill True

        frame:
            style "ui_overlay_frame"
            xalign 0.01
            yalign 0.02
            xsize 255
            vbox:
                spacing 4
                text "Panel" style "ui_text"
                textbutton ("Controls: ON" if app.show_controls else "Controls: OFF") action Function(app.toggle_controls) style "ui_button" text_style "ui_button_text"
                textbutton ("Map: ON" if app.show_map else "Map: OFF") action Function(app.toggle_map) style "ui_button" text_style "ui_button_text"
                textbutton ("Log: ON" if app.show_log else "Log: OFF") action Function(app.toggle_log) style "ui_button" text_style "ui_button_text"
                textbutton ("Tests: ON" if app.show_tests else "Tests: OFF") action Function(app.toggle_tests) style "ui_button" text_style "ui_button_text"
                if hasattr(app, "toggle_generator_ui"):
                    textbutton ("Generator UI: ON" if getattr(app, "show_generator_ui", False) else "Generator UI: OFF") action Function(app.toggle_generator_ui) style "ui_button" text_style "ui_button_text"
                textbutton "Exit" action Return() style "ui_button" text_style "ui_button_text"

        if hasattr(app, "tune_fov_minus"):
            $ _rv = app._renderer_vals() if hasattr(app, "_renderer_vals") else None
            frame:
                style "ui_overlay_frame"
                xalign 0.30
                yalign 0.02
                xsize 440
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
                        text ("Cols: %d" % (_rv["columns_cap"] if _rv else 0)) style "ui_text_small"
                        textbutton "-" action Function(app.tune_cols_minus) style "ui_button" text_style "ui_button_text"
                        textbutton "+" action Function(app.tune_cols_plus) style "ui_button" text_style "ui_button_text"

                    if _rv:
                        text ("Render: %.2f ms   Avg20: %.2f ms" % (_rv["render_ms_last"], _rv["render_ms_avg"])) style "ui_text_small"

                    hbox:
                        spacing 6
                        textbutton "Preset Home" action Function(app.tune_render_home) style "ui_button" text_style "ui_button_text"
                        textbutton "Reset" action Function(app.tune_render_reset) style "ui_button" text_style "ui_button_text"

        frame:
            style "ui_overlay_frame"
            xalign 0.5
            yalign 0.98
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

        if app.show_controls:
            frame:
                style "ui_overlay_frame"
                xalign 0.01
                yalign 0.33
                xsize 540
                vbox:
                    spacing 2
                    text "Status" style "ui_text"
                    text "Keys: W/S move, A/D strafe, Q/E turn, F interact" style "ui_text_small"
                    for line in app.hud_lines():
                        text line style "ui_text_small" substitute False

        if app.show_map:
            frame:
                style "ui_overlay_frame"
                xalign 0.99
                yalign 0.02
                xsize 520
                vbox:
                    spacing 4
                    text "ASCII Map" style "ui_text"
                    text app.ascii_map() style "ui_mono_map_text" substitute False

        if app.show_log:
            frame:
                style "ui_overlay_frame"
                xalign 0.99
                yalign 0.40
                xsize 520
                ysize 170
                vbox:
                    spacing 2
                    text "Log" style "ui_text"
                    for line in app.log[-10:]:
                        text line style "ui_text_small" substitute False

        if app.show_tests:
            frame:
                style "ui_overlay_frame"
                xalign 0.99
                yalign 0.68
                xsize 520
                ysize 285
                vbox:
                    spacing 4
                    text "Tests" style "ui_text"
                    hbox:
                        spacing 6
                        textbutton "Run All" action Function(app.do_run_all_tests) style "ui_button" text_style "ui_button_text"
                    viewport:
                        draggable True
                        mousewheel True
                        scrollbars "vertical"
                        ymaximum 205
                        vbox:
                            spacing 3
                            for tname in app.available_tests():
                                textbutton ("Run: %s" % tname) action Function(app.do_run_test, tname) style "ui_button" text_style "ui_button_text"
                            null height 4
                            if app.test_results:
                                text "Results:" style "ui_text_small"
                                for entry in app.test_results:
                                    $ name = entry[0]
                                    $ ok = entry[1]
                                    $ msg = entry[2] if len(entry) > 2 else ""
                                    $ mark = "OK" if ok else "FAIL"
                                    text ("%s: %s - %s" % (mark, name, msg)) style "ui_text_small" substitute False
                            else:
                                text "No tests run yet." style "ui_text_small"

        if hasattr(app, "show_generator_ui") and app.show_generator_ui:
            frame:
                style "ui_overlay_frame"
                xalign 0.62
                yalign 0.02
                xsize 330
                ysize 180
                vbox:
                    spacing 4
                    text "Generator" style "ui_text"
                    text "MVP floor-first" style "ui_text_small"
                    if hasattr(app, "do_gen_house_floor_mvp"):
                        textbutton "Generate house floor MVP" action Function(app.do_gen_house_floor_mvp) style "ui_button" text_style "ui_button_text"
                    if hasattr(app, "do_gen_demo_room"):
                        textbutton "Load demo room" action Function(app.do_gen_demo_room) style "ui_button" text_style "ui_button_text"
                    textbutton "Close" action Function(app.toggle_generator_ui) style "ui_button" text_style "ui_button_text"