import os
import yaml

def generate_dir_structure(path, indent=0):
    structure = {}
    for item in os.listdir(path):
        if item in ['.git', '.idea', '.venv', '__pycache__', 'node_modules']: # Exclude common VCS, IDE, virtual env, and build directories
            continue
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            structure[item + '/'] = generate_dir_structure(item_path, indent + 1)
        else:
            structure[item] = None # Represent files without further children
    return structure

if __name__ == "__main__":
    project_root = os.getcwd() # Get the current working directory (project root)
    dir_structure = generate_dir_structure(project_root)
    
    # Convert to YAML string
    yaml_output = yaml.dump(dir_structure, default_flow_style=False, indent=2)
    
    # Print to console, user can redirect this to a file
    print(yaml_output)
