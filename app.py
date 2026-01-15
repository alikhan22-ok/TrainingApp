import gradio as gr
from training import Training
import os

def get_program_choices(training):
    programs = training.list_programs()
    if not programs:
        return [], None
    return [(p['name'], p['id']) for p in programs], programs[0]['id']

def get_exercise_choices(training, program_id):
    if not program_id:
        return [], None
    try:
        exercises = training.list_exercises(program_id)
    except KeyError:
        return [], None
        
    if not exercises:
        return [], None
    return [(e['name'], e['id']) for e in exercises], exercises[0]['id']

def display_program(training, program_id):
    if not program_id:
        return "No program selected.", gr.update(choices=[], value=None)
    try:
        p = training.get_program(program_id)
    except Exception:
        return "No program selected.", gr.update(choices=[], value=None)
    
    out = f"Program: {p['name']}\n"
    if not p['exercises']:
        out += "  (No exercises.)"
        return out, gr.update(choices=[], value=None)
    
    for e in p['exercises']:
        out += f"\n  Exercise: {e['name']} (Reps: {e['rep_min']}-{e['rep_max']})"
        if not e['sets']:
            out += "\n    (No sets recorded)"
        for i, s in enumerate(e['sets']):
            out += f"\n    Set {i+1}: {s['weight']} lbs x {s['reps']} reps"
            
    exercises = [(e['name'], e['id']) for e in p['exercises']]
    ex_id = exercises[0][1] if exercises else None
    return out, gr.update(choices=exercises, value=ex_id)

def display_exercise(training, program_id, exercise_id):
    if not (program_id and exercise_id):
        return "No exercise selected.", 0.0
    try:
        exs = training.list_exercises(program_id)
        matches = [e for e in exs if e['id']==exercise_id]
        if not matches:
             return "Exercise not found.", 0.0
        e = matches[0]
    except Exception:
        return "No exercise selected.", 0.0
        
    out = f"{e['name']} (Reps: {e['rep_min']}-{e['rep_max']})"
    sets = e['sets']
    if not sets:
        out += "\n  No sets recorded yet."
    else:
        for i, s in enumerate(sets):
            out += f"\n  Set {i+1}: {s['weight']} lbs x {s['reps']} reps"
            
    suggested = training.get_suggested_weight(program_id, exercise_id)
    return out, suggested

def create_program_fn(training, prog_name):
    if not prog_name.strip():
        return gr.update(choices=[], value=None), "Enter a name.", "", gr.update(choices=[], value=None), "", 0.0
    pid = training.create_program(prog_name)
    programs, select_id = get_program_choices(training)
    display, exercises = display_program(training, pid)
    return gr.update(choices=programs, value=pid), "", display, gr.update(choices=[], value=None), "", 0.0

def rename_program_fn(training, prog_id, new_name):
    if not new_name.strip():
        return "", gr.update()
    try:
        training.rename_program(prog_id, new_name)
        display, _ = display_program(training, prog_id)
        return display, gr.update(value="")
    except Exception as e:
        return f"Error: {str(e)}", gr.update()

def delete_program_fn(training, prog_id):
    try:
        training.delete_program(prog_id)
    except Exception:
        pass
    programs, select_id = get_program_choices(training)
    if select_id:
        display, exercises = display_program(training, select_id)
        ex_disp = "" # Clear exercise display
        return gr.update(choices=programs, value=select_id), "", display, exercises, ex_disp, 0.0
    else:
        return gr.update(choices=[], value=None), "", "", gr.update(choices=[], value=None), "", 0.0

def select_program_fn(training, prog_id):
    display, exercise_dropdown = display_program(training, prog_id)
    if exercise_dropdown['choices']:
        ex_id = exercise_dropdown['value']
        ex_disp, sugg = display_exercise(training, prog_id, ex_id)
    else:
        ex_id = None
        ex_disp = ""
        sugg = 0.0
    exercises, _ = get_exercise_choices(training, prog_id)
    return display, gr.update(choices=exercises, value=ex_id), ex_disp, sugg

def add_exercise_fn(training, prog_id, ex_name, rep_min, rep_max):
    if not (prog_id and ex_name.strip()):
        return "", "", gr.update(), 0.0
    if rep_min > rep_max:
        rep_min, rep_max = rep_max, rep_min
    eid = training.add_exercise(prog_id, ex_name, rep_min, rep_max)
    display, exercise_dropdown = display_program(training, prog_id)
    exercises, exid = get_exercise_choices(training, prog_id)
    ex_disp, sugg = display_exercise(training, prog_id, eid)
    return display, ex_disp, gr.update(choices=exercises, value=eid), sugg

def rename_exercise_fn(training, prog_id, ex_id, new_ex_name):
    if not (prog_id and ex_id and new_ex_name.strip()):
        return "", gr.update(value="")
    try:
        training.rename_exercise(prog_id, ex_id, new_ex_name)
        ex_disp, sugg = display_exercise(training, prog_id, ex_id)
        display, _ = display_program(training, prog_id) 
        return display, ex_disp, gr.update(value="")
    except Exception as e:
        return "", f"Error: {str(e)}", gr.update()

def delete_exercise_fn(training, prog_id, ex_id):
    try:
        training.remove_exercise(prog_id, ex_id)
    except Exception:
        pass
    display, exercise_dropdown = display_program(training, prog_id)
    exercises, exid = get_exercise_choices(training, prog_id)
    if exercises:
        ex_id_new = exercises[0][1]
        ex_disp, sugg = display_exercise(training, prog_id, ex_id_new)
    else:
        ex_disp, sugg = "", 0.0
        exid = None
    return display, ex_disp, gr.update(choices=exercises, value=exid), sugg

def select_exercise_fn(training, prog_id, ex_id):
    ex_disp, sugg = display_exercise(training, prog_id, ex_id)
    return ex_disp, sugg, gr.update(value=sugg), gr.update(value=0)

def rep_options():
    return list(range(1, 26))

def set_options(training, prog_id, ex_id):
    if not (prog_id and ex_id):
        return [], None
    try:
        exs = training.list_exercises(prog_id)
        matches = [e for e in exs if e['id']==ex_id]
        if not matches:
            return [], None
        e = matches[0]
        set_choices = [ (f"Set {i+1}: {s['weight']}x{s['reps']}", s['id']) for i, s in enumerate(e['sets'])]
        return set_choices, set_choices[-1][1] if set_choices else None
    except Exception:
        return [], None

def add_set_fn(training, prog_id, ex_id, weight, reps):
    if not (prog_id and ex_id):
        return "", "", 0.0
    try:
        set_id = training.add_set(prog_id, ex_id, float(weight), int(reps))
        ex_disp, sugg = display_exercise(training, prog_id, ex_id)
        prog_disp, _ = display_program(training, prog_id)
        return prog_disp, ex_disp, sugg
    except Exception as e:
        return f"Error: {str(e)}", "", 0.0

def edit_set_fn(training, prog_id, ex_id, set_id, weight, reps):
    if not (prog_id and ex_id and set_id):
        return "", "", 0.0
    try:
        training.edit_set(prog_id, ex_id, set_id, float(weight), int(reps))
        ex_disp, sugg = display_exercise(training, prog_id, ex_id)
        prog_disp, _ = display_program(training, prog_id)
        return prog_disp, ex_disp, sugg
    except Exception as e:
        return f"Error: {str(e)}", "", 0.0

def remove_set_fn(training, prog_id, ex_id, set_id):
    if not (prog_id and ex_id and set_id):
        return "", "", 0.0
    try:
        training.remove_set(prog_id, ex_id, set_id)
        ex_disp, sugg = display_exercise(training, prog_id, ex_id)
        prog_disp, _ = display_program(training, prog_id)
        return prog_disp, ex_disp, sugg
    except Exception as e:
        return f"Error: {str(e)}", "", 0.0

### App Initialization
training = Training(data_file='workout_data.json')

with gr.Blocks(title="Workout Program Manager") as demo:
    gr.Markdown("## Workout Program Manager\nCreate programs, add exercises, and track your sets. Data is saved automatically.")
    
    with gr.Row():
        # Program mgmt
        with gr.Column(scale=1):
            gr.Markdown("### 1. Programs")
            prog_dropdown = gr.Dropdown(label="Select Program", choices=[], interactive=True)
            prog_name_in = gr.Textbox(label="New Program Name", placeholder="e.g. Strength A")
            with gr.Row():
                create_prog_btn = gr.Button("Create", variant="primary")
                delete_prog_btn = gr.Button("Delete")
            with gr.Row():
                rename_prog_in = gr.Textbox(show_label=False, placeholder="Rename current program...", container=False)
                rename_prog_btn = gr.Button("Rename")
            prog_disp = gr.Textbox(label="Program Overview", lines=10, interactive=False)
            
        # Exercise mgmt
        with gr.Column(scale=1):
            gr.Markdown("### 2. Exercises")
            ex_dropdown = gr.Dropdown(label="Select Exercise", choices=[], interactive=True)
            ex_name_in = gr.Textbox(label="New Exercise Name", placeholder="e.g. Bench Press")
            with gr.Row():
                rep_min_dropdown = gr.Dropdown(label="Min Reps", choices=rep_options(), value=8)
                rep_max_dropdown = gr.Dropdown(label="Max Reps", choices=rep_options(), value=12)
            with gr.Row():
                add_ex_btn = gr.Button("Add Exercise", variant="primary")
                delete_ex_btn = gr.Button("Delete")
            with gr.Row():
                 rename_ex_in = gr.Textbox(show_label=False, placeholder="Rename current exercise...", container=False)
                 rename_ex_btn = gr.Button("Rename")
            ex_disp = gr.Textbox(label="Exercise History", lines=10, interactive=False)
            
        # Set mgmt
        with gr.Column(scale=1):
            gr.Markdown("### 3. Log Sets")
            set_dropdown = gr.Dropdown(label="Select Set to Edit", choices=[], interactive=True)
            with gr.Row():
                weight_in = gr.Number(label="Weight (lbs)", value=0.0)
                reps_in = gr.Number(label="Reps", value=0, precision=0)
            suggested_weight_box = gr.Number(label="Suggested Next Weight", value=0.0, interactive=False)
            with gr.Row():
                add_set_btn = gr.Button("Log Set", variant="primary")
                edit_set_btn = gr.Button("Update Set")
                remove_set_btn = gr.Button("Delete Set")

    # Initial Population
    def startup_populate():
        programs, prog_id = get_program_choices(training)
        exercises, ex_id = get_exercise_choices(training, prog_id)
        
        prog_disp_str = ""
        ex_disp_str = ""
        sugg = 0.0
        
        if prog_id:
            prog_disp_str, _ = display_program(training, prog_id)
            if ex_id:
                ex_disp_str, sugg = display_exercise(training, prog_id, ex_id)
        
        set_choices, set_id = set_options(training, prog_id, ex_id)
        
        return (gr.update(choices=programs, value=prog_id),           
                gr.update(choices=exercises, value=ex_id),            
                prog_disp_str,                                        
                ex_disp_str,                                          
                gr.update(choices=set_choices, value=set_id),         
                sugg,                                                 
                sugg, # pre-fill weight with suggestion
                0,                                                    
                "", "", "", "")

    demo.load(startup_populate, outputs=[prog_dropdown, ex_dropdown, prog_disp, ex_disp, set_dropdown, suggested_weight_box, weight_in, reps_in, prog_name_in, rename_prog_in, ex_name_in, rename_ex_in])

    # Event Handlers
    create_prog_btn.click(fn=lambda prog_name: create_program_fn(training, prog_name),
                         inputs=[prog_name_in],
                         outputs=[prog_dropdown, prog_name_in, prog_disp, ex_dropdown, ex_disp, suggested_weight_box])
    
    rename_prog_btn.click(lambda pid, newname: rename_program_fn(training, pid, newname),
                         inputs=[prog_dropdown, rename_prog_in],
                         outputs=[prog_disp, rename_prog_in])
    
    delete_prog_btn.click(lambda pid: delete_program_fn(training, pid),
                         inputs=[prog_dropdown],
                         outputs=[prog_dropdown, prog_name_in, prog_disp, ex_dropdown, ex_disp, suggested_weight_box])
    
    prog_dropdown.change(lambda pid: select_program_fn(training, pid),
                         inputs=[prog_dropdown],
                         outputs=[prog_disp, ex_dropdown, ex_disp, suggested_weight_box])

    add_ex_btn.click(lambda prog_id, ex_name, rmin, rmax: add_exercise_fn(training, prog_id, ex_name, rmin, rmax),
                    inputs=[prog_dropdown, ex_name_in, rep_min_dropdown, rep_max_dropdown],
                    outputs=[prog_disp, ex_disp, ex_dropdown, suggested_weight_box])
    
    rename_ex_btn.click(lambda pid, exid, newexname: rename_exercise_fn(training, pid, exid, newexname),
                      inputs=[prog_dropdown, ex_dropdown, rename_ex_in],
                      outputs=[prog_disp, ex_disp, rename_ex_in])
    
    delete_ex_btn.click(lambda pid, exid: delete_exercise_fn(training, pid, exid),
                      inputs=[prog_dropdown, ex_dropdown],
                      outputs=[prog_disp, ex_disp, ex_dropdown, suggested_weight_box])
    
    ex_dropdown.change(lambda pid, exid: select_exercise_fn(training, pid, exid),
                     inputs=[prog_dropdown, ex_dropdown],
                     outputs=[ex_disp, suggested_weight_box, weight_in, reps_in])

    def update_set_dropdown(prog_id, ex_id):
        set_choices, set_id = set_options(training, prog_id, ex_id)
        return gr.update(choices=set_choices, value=set_id)

    ex_dropdown.change(update_set_dropdown, inputs=[prog_dropdown, ex_dropdown], outputs=[set_dropdown])

    add_set_btn.click(lambda prog_id, ex_id, wt, r: add_set_fn(training, prog_id, ex_id, wt, r),
                   inputs=[prog_dropdown, ex_dropdown, weight_in, reps_in],
                   outputs=[prog_disp, ex_disp, suggested_weight_box])
    
    # Reload set dropdown after adding/editing sets
    add_set_btn.click(update_set_dropdown, inputs=[prog_dropdown, ex_dropdown], outputs=[set_dropdown])
    
    set_dropdown.change(lambda pid, exid: update_set_dropdown(pid, exid), 
                      inputs=[prog_dropdown, ex_dropdown], outputs=[set_dropdown])
    
    edit_set_btn.click(lambda pid, exid, sid, wt, r: edit_set_fn(training, pid, exid, sid, wt, r),
                    inputs=[prog_dropdown, ex_dropdown, set_dropdown, weight_in, reps_in],
                    outputs=[prog_disp, ex_disp, suggested_weight_box])
    edit_set_btn.click(update_set_dropdown, inputs=[prog_dropdown, ex_dropdown], outputs=[set_dropdown])

    remove_set_btn.click(lambda pid, exid, sid: remove_set_fn(training, pid, exid, sid),
                       inputs=[prog_dropdown, ex_dropdown, set_dropdown],
                       outputs=[prog_disp, ex_disp, suggested_weight_box])
    remove_set_btn.click(update_set_dropdown, inputs=[prog_dropdown, ex_dropdown], outputs=[set_dropdown])

if __name__ == "__main__":
    demo.launch()