import bpy


def update_space(source_space, target_space):
    def update_attributes(source, target, attributes):
        for attribute in attributes:
            new_attribute = getattr(source, attribute, None)
            if new_attribute is not None:
                setattr(target, attribute, new_attribute)

    # Update space attributes, causes 2 additional redraws on target
    space_attributes = ['clip_end', 'clip_start', 'lens']
    update_attributes(source_space, target_space, space_attributes)
    # Update ViewRegion3D attributes
    # All modifiable attributes, causes 8 additional redraws on target
    view_region_3d_attributes = ['clip_planes', 'is_orthographic_side_view', 'is_perspective', 'lock_rotation', 'show_sync_view', 'use_box_clip', 'use_clip_planes',
                                 'view_camera_offset', 'view_camera_zoom', 'view_distance', 'view_location', 'view_perspective', 'view_rotation']
    update_attributes(source_space.region_3d, target_space.region_3d, view_region_3d_attributes)

# Issue: Our modal operator to report our mouse position is removed on loading a new file, and does not work on a new window


class SyncDrawHandler:
    def __init__(self):
        self.add_handler()
        self.source_area = None
        self.mouse_pos = (0, 0)
        self.skip_sync = False

    # Handler order: PRE_VIEW, POST_VIEW, POST_PIXEL
    def add_handler(self):
        self.handlers = []
        self.handlers.append(bpy.types.SpaceView3D.draw_handler_add(
            self.sync_draw_callback, (), 'WINDOW', 'PRE_VIEW'))

    def has_handlers(self):
        return len(self.handlers) > 0

    def update_mouse_pos(self, mouse_pos):
        self.mouse_pos = mouse_pos

    def mouse_is_in_area(self, area_window_min, area_window_max):
        return not ((self.mouse_pos[0] < area_window_min[0]) or (self.mouse_pos[0] > area_window_max[0]) or (self.mouse_pos[1] < area_window_min[1]) or (self.mouse_pos[1] > area_window_max[1]))

    def sync_draw_callback(self):
        context = bpy.context
        area_window_min = (context.area.x, context.area.y)
        area_window_max = (context.area.x + context.area.width, context.area.y + context.area.height)
        if not bpy.context.region_data.show_sync_view:
            return

        this_area = context.area

        # Small optimization: Python evaluates conditions lazily, so if first conditions succeeds we don't need to do any work to check the second condition
        if self.source_area == this_area or self.mouse_is_in_area(area_window_min, area_window_max):
            # For some reason updating another viewport causes this viewport to have an additional redraw, so we skip
            if self.skip_sync:
                self.skip_sync = False
                return
            self.skip_sync = True

            self.source_area = this_area
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == "VIEW_3D" and area != this_area:
                        if area.spaces[0].region_3d.show_sync_view:
                            update_space(this_area.spaces[0], area.spaces[0])

        return

    def remove_handler(self):
        for handler in self.handlers:
            bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
        self.handlers = []
