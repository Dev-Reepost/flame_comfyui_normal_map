# ComFlameUI Normal Map DeepBump

An Autodesk Pybox handler integrating ComfyUI DeepBump Normal Map workflows

## Inputs

- `Front` input to ComfyUI EXR loader
  - The image coming from Flame batch upstream node

Input images are written on the ComfyUI server disk
`<COMFYUI_SERVER_MOUNTING>/in/<FLAME_PROJECT>/normal_map_deepbump/`

## Outputs

- `Result` output from ComfyUI EXR Saver
  - The normal map of the source image
  
Output images are read on the ComfyUI server disk
`<COMFYUI_SERVER_MOUNTING>/out/<FLAME_PROJECT>/normal_map_deepbump/`
