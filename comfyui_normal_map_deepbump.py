##########################################################################
#
# Filename: comfyui_zdepth.py
#
# Author: Julien Martin
# Created: 2024-03
#
###########################################################################
from __future__ import print_function

import sys
import json
import webbrowser

import pybox_v1 as pybox
import pybox_comfyui

from pybox_comfyui import UI_INTERRUPT
from pybox_comfyui import Color
from pybox_comfyui import LayerIn
from pybox_comfyui import LayerOut


COMFYUI_WORKFLOW_NAME = "ComfyUI Normal Map DeepBump"
COMFYUI_OPERATOR_NAME = "normal_map_deepbump"

UI_MODE = "Mode"
UI_COLOR_TO_NORMALS_OVERLAP = "Colors to Normals Overlap"
UI_NORMALS_TO_CURVATURE_BLUR_RADIUS = "Normals to Curvature Blur Radius"
UI_NORMALS_TO_HEIGHT_SEAMLESS = "Normals to Height Seamless"

DEFAULT_MODE = "Color to Normals"
DEFAULT_COLOR_TO_NORMALS_OVERLAP = "SMALL"
DEFAULT_NORMALS_TO_CURVATURE_BLUR_RADIUS = "SMALLEST"
DEFAULT_NORMALS_TO_HEIGHT_SEAMLESS = True


class ComfyuiNMDB(pybox_comfyui.ComfyUIBaseClass):
    operator_name = COMFYUI_OPERATOR_NAME
    operator_layers = [LayerIn.FRONT, LayerOut.RESULT]
    
    version = 1
    
    workflow_deepbump_idx = -1
    # workflow_mode_idx = -1
    # workflow_colors_to_normals_overlap_idx = -1
    # workflow_normals_to_curvature_blur_radius_idx = -1
    # workflow_normals_to_height_seamless_idx = -1
    
    mode = DEFAULT_MODE
    colors_to_normals_overlap = DEFAULT_COLOR_TO_NORMALS_OVERLAP
    normals_to_curvature_blur_radius = DEFAULT_NORMALS_TO_CURVATURE_BLUR_RADIUS
    normals_to_height_seamless = DEFAULT_NORMALS_TO_HEIGHT_SEAMLESS
    
    modes = ["Color to Normals",
            "Normals to Curvature",
            "Normals to Height"]
    
    colors_to_normals_overlaps = ["SMALL", 
                                "MEDIUM", 
                                "LARGE"]

    normals_to_curvature_blur_radiuses = ["SMALLEST", 
                                        "SMALLER",
                                        "SMALL",
                                        "MEDIUM",
                                        "LARGE",
                                        "LARGER",
                                        "LARGEST"]
    
    
    ###########################################################################
    # Overrided functions from pybox_comfyui.ComfyUIBaseClass
    
    
    def initialize(self):
        super().initialize()
        
        self.set_state_id("setup_ui")
        self.setup_ui()


    def setup_ui(self):
        super().setup_ui()
        
        self.set_state_id("execute")
    
    
    def execute(self):
        super().execute()
        
        if self.out_frame_requested():
                self.submit_workflow()
        
        if self.get_global_element_value(UI_INTERRUPT):
            self.interrupt_workflow()

        self.update_workflow_execution()
        self.update_outputs(layers=self.operator_layers)
    
    
    def teardown(self):
        super().teardown()
    
    
    ###########################################################################
    # Node-specific functions
    
    ###################################
    # UI
    
    def init_ui(self):
        
        # ComfyUI pages
        pages = []
        page = pybox.create_page(
            COMFYUI_WORKFLOW_NAME, 
            "Server & Workflow", "Parameters", "Action"
            )
        pages.append(page)
        self.set_ui_pages_array(pages)
        
        col = 0
        self.set_ui_host_info(col)
        
        self.set_ui_workflow_path(col, self.workflow_dir, self.workflow_path)
        
        col = 1
        mode = pybox.create_popup(
            UI_MODE, 
            self.modes, 
            value=self.modes.index(self.mode), 
            default=0, 
            row=0, col=col, tooltip=UI_MODE
            )
        self.add_global_elements(mode)
        
        ctno = pybox.create_popup(
            UI_COLOR_TO_NORMALS_OVERLAP, 
            self.colors_to_normals_overlaps, 
            value=self.colors_to_normals_overlaps.index(self.colors_to_normals_overlap), 
            default=0, 
            row=1, col=col, tooltip=UI_COLOR_TO_NORMALS_OVERLAP
            )
        self.add_global_elements(ctno)
        
        ntcbr = pybox.create_popup(
            UI_NORMALS_TO_CURVATURE_BLUR_RADIUS, 
            self.normals_to_curvature_blur_radiuses, 
            value=self.normals_to_curvature_blur_radiuses.index(self.normals_to_curvature_blur_radius), 
            default=0, 
            row=2, col=col, tooltip=UI_NORMALS_TO_CURVATURE_BLUR_RADIUS
            )
        self.add_global_elements(ntcbr)
        
        nths = pybox.create_toggle_button(
            UI_NORMALS_TO_HEIGHT_SEAMLESS, 
            self.normals_to_height_seamless, 
            default=True,
            row=3, col=col, tooltip=UI_NORMALS_TO_HEIGHT_SEAMLESS
            )
        self.add_global_elements(nths)
        
        col = 2
        # ComfyUI workflow actions
        self.ui_version_row = 0
        self.ui_version_col = col
        self.set_ui_versions()
        
        self.set_ui_increment_version(row=1, col=col)

        self.set_ui_interrupt(row=2, col=col)
        
        self.ui_processing_color_row = 3
        self.ui_processing_color_col = col
        self.set_ui_processing_color(Color.GRAY, self.ui_processing)
    
    
    def set_models(self):
        pass
    
    ###################################
    # Workflow
    
    def load_workflow(self):
        with open(self.workflow_path) as f:
            print("Loading Workflow")
            self.workflow = json.load(f)
            self.workflow_id_to_class_type = {id: details['class_type'] for id, details in self.workflow.items()}
            # load & save 
            self.workflow_load_exr_front_idx = self.get_workflow_index('LoadEXR')
            wf_ids_to_classes = self.workflow_id_to_class_type.items()
            save_exr_nodes = [(key, self.workflow.get(key)["inputs"]) for key, value in wf_ids_to_classes if value == 'SaveEXR']
            self.workflow_save_exr_result_idx = [key for (key, attr) in save_exr_nodes if attr["filename_prefix"] == "Result"][0]
            # paramaters
            self.workflow_deepbump_idx = self.get_workflow_index('Deep Bump (mtb)')
            self.mode = self.workflow.get(self.workflow_deepbump_idx)["inputs"]["mode"]
            self.color_to_normals_overlap = self.workflow.get(self.workflow_deepbump_idx)["inputs"]["color_to_normals_overlap"]
            self.normals_to_curvature_blur_radius = self.workflow.get(self.workflow_deepbump_idx)["inputs"]["normals_to_curvature_blur_radius"]
            self.normals_to_height_seamless = self.workflow.get(self.workflow_deepbump_idx)["inputs"]["normals_to_height_seamless"]
            
            self.out_frame_pad = self.workflow.get(self.workflow_save_exr_result_idx)["inputs"]["frame_pad"]
    
    
    def set_workflow_mode(self):
        if self.workflow:  
            self.mode = self.modes[int(self.get_global_element_value(UI_MODE))]
            self.workflow.get(self.workflow_deepbump_idx)["inputs"]["mode"] = self.mode
            print(f'Workflow {UI_MODE}: {self.mode}')
    
    
    def set_workflow_color_to_normals_overlap(self):
        if self.workflow:  
            self.color_to_normals_overlap = self.colors_to_normals_overlaps[int(self.get_global_element_value(UI_COLOR_TO_NORMALS_OVERLAP))]
            self.workflow.get(self.workflow_deepbump_idx)["inputs"]["color_to_normals_overlap"] = self.color_to_normals_overlap
            print(f'Workflow {UI_COLOR_TO_NORMALS_OVERLAP}: {self.color_to_normals_overlap}')
    
    
    def set_workflow_normals_to_curvature_blur_radius(self):
        if self.workflow:  
            self.normals_to_curvature_blur_radius = self.normals_to_curvature_blur_radiuses[int(self.get_global_element_value(UI_NORMALS_TO_CURVATURE_BLUR_RADIUS))]
            self.workflow.get(self.workflow_deepbump_idx)["inputs"]["normals_to_curvature_blur_radius"] = self.normals_to_curvature_blur_radius
            print(f'Workflow {UI_NORMALS_TO_CURVATURE_BLUR_RADIUS}: {self.normals_to_curvature_blur_radius}')
    
    
    def set_workflow_normals_to_height_seamless(self):
        if self.workflow:  
            self.normals_to_height_seamless = self.get_global_element_value(UI_NORMALS_TO_HEIGHT_SEAMLESS)
            self.workflow.get(self.workflow_deepbump_idx)["inputs"]["normals_to_height_seamless"] = self.normals_to_height_seamless
            print(f'Workflow {UI_NORMALS_TO_HEIGHT_SEAMLESS}: {self.normals_to_height_seamless}')    
    
    
    def workflow_setup(self):
        
        self.set_workflow_mode()
        self.set_workflow_color_to_normals_overlap()
        self.set_workflow_normals_to_curvature_blur_radius()
        self.set_workflow_normals_to_height_seamless()
        
        self.set_workflow_load_exr_filepath()
        self.set_workflow_save_exr_filename_prefix(layers=self.operator_layers)
    
    
    
def _main(argv):
    print("____________________")
    print("Loading ComfyUI JSON Pybox")
    print("____________________")
    
    # Load the json file, make sure you have read access to it
    p = ComfyuiNMDB(argv[0])
    # Call the appropriate function
    p.dispatch()
    # Save file
    p.write_to_disk(argv[0])
    
    print("____________________")
    print("Writing ComfyUI JSON Pybox")
    print("____________________")

if __name__ == "__main__":
    _main(sys.argv[1:])
    