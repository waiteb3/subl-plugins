import sublime
import sublime_plugin
import os

# TODO use this which was borrowed from gitignore plugin
def windows_path_to_sublime_path(path):
    """
    Removes the colon after the drive letter and replaces backslashes with
    slashes.

    e.g.

        windows_path_to_sublime_path("C:\somedir\somefile")
        == "C/somedir/somefile"
    """
    assert(path[1] == u':')
    without_colon = path[0] + path[2:]
    return without_colon.replace(u'\\', u'/')

def find_gitignores(folder):
    """
    Returns a list of all nested gitignores in a folder.
    """
    return [root for root, subfolders, files
                 in os.walk(folder)
                 if '.gitignore' in files]

def update_exclude_patterns(window):
    """
    Based on the current project, scrape up the gitignores and add their rules
    to the folder_exclude_patterns value in the project for each folder
    """
    print("--------------%s-------------" % "here")

    project_data = window.project_data()

    # TODO ephemeral projects
    project_path = window.extract_variables()["project_path"]

    for folder in project_data["folders"]:
        # save any manually/previously set patterns
        if "existing_folder_exclude_patterns" not in folder:
            if "folder_exclude_patterns" in folder:
                existing = list(folder["folder_exclude_patterns"])
            else:
                existing = list()

            folder["existing_folder_exclude_patterns"] = existing

        folder["folder_exclude_patterns"] = list(folder["existing_folder_exclude_patterns"])

        if "existing_file_exclude_patterns" not in folder:
            if "file_exclude_patterns" in folder:
                existing = list(folder["file_exclude_patterns"])
            else:
                existing = list()

            folder["existing_file_exclude_patterns"] = existing

        folder["file_exclude_patterns"] = list(folder["existing_file_exclude_patterns"])

        ignore_folders = []
        ignore_files = []

        folder_path = os.path.normpath(os.path.join(project_path, folder["path"]))

        for path in find_gitignores(folder_path):
            gitignore = path + "/.gitignore"
            for line in open(gitignore, "r").readlines():
                line = line.strip()

                if line == "" or line.startswith("#"):
                    continue

                # Three cases:
                # startswith /, means the folder at this root should be ignored
                # contains a /, means it's a folder to be ignored
                # else, it's a filetype or a folder, so add to both
                if line.startswith("/"):
                    ignore_folders.append(os.path.join(path, line[1:]))
                elif "/" in line:
                    ignore_folders.append(os.path.join(path, line))
                else:
                    ignore_folders.append(line)
                    ignore_files.append(line)

        # list(set(x)) removes duplicates
        folder["folder_exclude_patterns"] += list(set(ignore_folders))
        folder["file_exclude_patterns"] += list(set(ignore_files))

    window.set_project_data(project_data)

class GitignoreListener(sublime_plugin.EventListener):
    def on_post_save_async(self, view):
        """
        Updates the exclude patterns for a project only if the file saved was a .gitignore
        """
        if view.file_name().endswith(".gitignore"):
            update_exclude_patterns(view.window())

# TODO on start
def plugin_loaded():
    update_exclude_patterns(sublime.active_window())

# TODO on project switch

