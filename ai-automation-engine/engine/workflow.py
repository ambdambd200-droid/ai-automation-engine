import yaml
import os
from .actions import execute_action, ActionError
from storage.database import Database


class WorkflowEngine:
    def __init__(self, config):
        self.config = config
        self.db = Database(config.get("database", {}).get("path", "storage/data.db"))
        self.workflows_dir = config.get("workflows_dir", "workflows")
        self._loaded = {}

    def load_workflows(self):
        if not os.path.isdir(self.workflows_dir):
            return
        for fname in os.listdir(self.workflows_dir):
            if fname.endswith((".yaml", ".yml")):
                path = os.path.join(self.workflows_dir, fname)
                with open(path, encoding="utf-8") as f:
                    wf = yaml.safe_load(f)
                if wf and "workflow" in wf:
                    name = wf["workflow"].get("name") or fname.replace(".yaml", "").replace(".yml", "")
                    self._loaded[name] = wf

    def get_workflow(self, name):
        return self._loaded.get(name)

    def list_workflows(self):
        return list(self._loaded.keys())

    def run_workflow(self, name, input_data=None):
        wf = self.get_workflow(name)
        if not wf:
            raise ValueError(f"Workflow '{name}' not found")

        exec_id = self.db.create_execution(name, input_data)
        context = {"input": input_data or {}, "execution_id": exec_id}

        wf_config = wf["workflow"]
        steps = wf_config.get("steps", [])
        status = "completed"

        try:
            for i, step in enumerate(steps):
                step_name = step.get("name", f"step_{i}")
                self.db.add_log(exec_id, step_name, f"Starting step: {step_name}")

                try:
                    result = execute_action(step["action"], context)
                    context[f"step_{i}_result"] = result
                    context[f"steps.{step_name}"] = result
                    self.db.add_log(exec_id, step_name, f"Completed successfully")
                except ActionError as e:
                    self.db.add_log(exec_id, step_name, f"Action error: {e}", "error")
                    if step.get("on_error") == "stop":
                        status = "failed"
                        break
                    context[f"step_{i}_error"] = str(e)

            self.db.complete_execution(exec_id, status, context.get("last_response") or context.get("last_ai_response"))
        except Exception as e:
            self.db.add_log(exec_id, "engine", f"Fatal error: {e}", "error")
            self.db.complete_execution(exec_id, "failed", {"error": str(e)})
            raise

        return {"execution_id": exec_id, "status": status, "workflow": name}
