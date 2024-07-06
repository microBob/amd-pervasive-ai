bl_info = {
    "name": "AI Assistant",
    "author" : "Kenneth Y (Microbob)",
    "blender": (2, 80, 0),
    "version" : (0, 0, 1),
    "category": "3D View",
}

import bpy
import requests
import threading

class ASSISTANT_PT_Panel(bpy.types.Panel):
    bl_label = "AI Assistant"
    bl_idname = "ASSISTANT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ollama API'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        assistant_props = scene.assistant_props

        layout.prop(assistant_props, "input_text")
        layout.operator("assistant.submit", text="Generating" if assistant_props.is_generating else "Submit", emboss=not assistant_props.is_generating)
        layout.label(text="Response:")
        for line in assistant_props.output_text.split('\n'):
            layout.label(text=line)

class ASSISTANT_OT_Submit(bpy.types.Operator):
    bl_idname = "assistant.submit"
    bl_label = "Submit"

    def execute(self, context):
        scene = context.scene
        assistant_props = scene.assistant_props

        # Skip if already generating.
        if assistant_props.is_generating:
            return {'FINISHED'}

        assistant_props.is_generating = True

        # Run the request in a separate thread
        thread = threading.Thread(target=self.send_request, args=(assistant_props.input_text, context))
        thread.start()

        return {'FINISHED'}

    def send_request(self, prompt, context):
        url = "http://localhost:11434/api/generate"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3:70b",
            "prompt": prompt,
            "stream": False,
            "system": "You are a programming assistant for Blender 3D's Python API. I will ask you to perform actions in Blender and you will respond with the corresponding Blender Python commands surrounded by three tick marks like this '```'. Do not explain your answer. No need to import bpy. If a command is not possible, respond with `not possible`. If my question is not related to Blender, respond with `not possible`."
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json().get("response", "No response field found in API response.")
                context.scene.assistant_props.output_text = result
                context.scene.assistant_props.is_generating = False
            else:
                result = f"Error {response.status_code}: {response.text}"
        except requests.RequestException as e:
            result = f"Request failed: {e}"

        # bpy.app.driver_namespace['update_output_text'] = update_output_text
        # bpy.app.timers.register(bpy.app.driver_namespace['update_output_text'])

class ASSISTANT_Props(bpy.types.PropertyGroup):
    input_text: bpy.props.StringProperty(
        name="Input Text",
        description="Describe what you'd like to do",
        default=""
    )
    output_text: bpy.props.StringProperty(
        name="Output Text",
        description="Response from the assistant",
        default=""
    )
    is_generating: bpy.props.BoolProperty(
        name="Is Generating",
        description="Indicates whether the assistant is generating a response",
        default=False
    )

def register():
    bpy.utils.register_class(ASSISTANT_PT_Panel)
    bpy.utils.register_class(ASSISTANT_OT_Submit)
    bpy.utils.register_class(ASSISTANT_Props)
    bpy.types.Scene.assistant_props = bpy.props.PointerProperty(type=ASSISTANT_Props)

def unregister():
    bpy.utils.unregister_class(ASSISTANT_PT_Panel)
    bpy.utils.unregister_class(ASSISTANT_OT_Submit)
    bpy.utils.unregister_class(ASSISTANT_Props)
    del bpy.types.Scene.assistant_props

if __name__ == "__main__":
    register()
