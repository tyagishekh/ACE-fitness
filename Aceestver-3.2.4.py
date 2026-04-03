import json
import tkinter as tk
from tkinter import messagebox, ttk
from urllib import error, request


DEFAULT_API_BASE_URL = "http://127.0.0.1:5000"


class AceestApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def set_base_url(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _call(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with request.urlopen(req, timeout=5) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            message = f"HTTP {exc.code}"
            if body:
                try:
                    parsed = json.loads(body)
                    message = parsed.get("error", message)
                except json.JSONDecodeError:
                    message = body
            raise RuntimeError(message) from exc
        except error.URLError as exc:
            raise RuntimeError(
                "Could not connect to the Flask API. Start app.py first and check the API URL."
            ) from exc

    def health(self) -> dict:
        return self._call("GET", "/health")

    def get_programs(self) -> dict:
        return self._call("GET", "/programs")

    def get_members(self) -> list[dict]:
        return self._call("GET", "/members").get("members", [])

    def get_stats(self) -> dict:
        return self._call("GET", "/stats")

    def add_member(self, payload: dict) -> dict:
        return self._call("POST", "/members", payload)


class ACEestFrontend:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ACEest Fitness Desktop Client")
        self.root.geometry("1280x820")
        self.root.configure(bg="#111111")

        self.api = AceestApiClient(DEFAULT_API_BASE_URL)
        self.program_catalog: dict[str, dict] = {}
        self.member_rows: list[dict] = []

        self._configure_style()
        self._build_layout()
        self.load_initial_data()

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#111111")
        style.configure("TLabelframe", background="#111111", foreground="#d4af37")
        style.configure("TLabelframe.Label", background="#111111", foreground="#d4af37")
        style.configure("TLabel", background="#111111", foreground="#f5f5f5")
        style.configure("Treeview", background="#1f1f1f", foreground="#f5f5f5", fieldbackground="#1f1f1f")
        style.configure("Treeview.Heading", background="#d4af37", foreground="#111111", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#6f5a18")])
        style.configure("Accent.TButton", background="#d4af37", foreground="#111111", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#f0cc4d")])

    def _build_layout(self) -> None:
        header = tk.Frame(self.root, bg="#d4af37", height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="ACEest Fitness & Gym",
            font=("Segoe UI", 24, "bold"),
            bg="#d4af37",
            fg="#111111",
        ).pack(anchor="w", padx=24, pady=(16, 0))
        tk.Label(
            header,
            text="Tkinter frontend connected to the Flask API",
            font=("Segoe UI", 11),
            bg="#d4af37",
            fg="#222222",
        ).pack(anchor="w", padx=24)

        body = ttk.Frame(self.root, padding=18)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(1, weight=1)

        self._build_connection_panel(body)
        self._build_form_panel(body)
        self._build_members_panel(body)
        self._build_detail_panel(body)

        status_bar = tk.Frame(self.root, bg="#1a1a1a")
        status_bar.pack(fill="x")
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            bg="#1a1a1a",
            fg="#d4af37",
            anchor="w",
            padx=12,
            pady=8,
        ).pack(fill="x")

    def _build_connection_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="API Connection", padding=14)
        panel.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, text="Base URL").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.base_url_var = tk.StringVar(value=DEFAULT_API_BASE_URL)
        ttk.Entry(panel, textvariable=self.base_url_var).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(panel, text="Test Connection", style="Accent.TButton", command=self.test_connection).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(panel, text="Refresh Data", command=self.load_initial_data).grid(row=0, column=3)

        self.connection_state_var = tk.StringVar(value="Not checked")
        ttk.Label(panel, textvariable=self.connection_state_var).grid(row=1, column=0, columnspan=4, sticky="w", pady=(10, 0))

    def _build_form_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Add Gym User", padding=16)
        panel.grid(row=1, column=0, sticky="ns", padx=(0, 14))

        self.name_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.weight_var = tk.StringVar()
        self.adherence_var = tk.StringVar(value="80")
        self.goal_var = tk.StringVar()
        self.membership_var = tk.StringVar(value="active")

        fields = [
            ("Full Name", self.name_var),
            ("Age", self.age_var),
            ("Weight (kg)", self.weight_var),
            ("Adherence Score", self.adherence_var),
        ]

        for row_index, (label, variable) in enumerate(fields):
            ttk.Label(panel, text=label).grid(row=row_index * 2, column=0, sticky="w", pady=(0, 4))
            ttk.Entry(panel, textvariable=variable, width=28).grid(row=row_index * 2 + 1, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(panel, text="Goal").grid(row=8, column=0, sticky="w", pady=(0, 4))
        self.goal_box = ttk.Combobox(panel, textvariable=self.goal_var, state="readonly", width=26)
        self.goal_box.grid(row=9, column=0, sticky="ew", pady=(0, 10))
        self.goal_box.bind("<<ComboboxSelected>>", self.update_goal_hint)

        ttk.Label(panel, text="Membership Status").grid(row=10, column=0, sticky="w", pady=(0, 4))
        membership_box = ttk.Combobox(
            panel,
            textvariable=self.membership_var,
            values=("active", "inactive"),
            state="readonly",
            width=26,
        )
        membership_box.grid(row=11, column=0, sticky="ew", pady=(0, 10))

        self.goal_hint_var = tk.StringVar(value="Choose a goal to see the suggested training focus.")
        tk.Label(
            panel,
            textvariable=self.goal_hint_var,
            bg="#161616",
            fg="#cfcfcf",
            justify="left",
            wraplength=260,
            padx=12,
            pady=12,
        ).grid(row=12, column=0, sticky="ew", pady=(6, 12))

        button_row = ttk.Frame(panel)
        button_row.grid(row=13, column=0, sticky="ew")
        ttk.Button(button_row, text="Add User", style="Accent.TButton", command=self.submit_member).pack(side="left")
        ttk.Button(button_row, text="Clear", command=self.clear_form).pack(side="left", padx=(8, 0))

    def _build_members_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Registered Users", padding=14)
        panel.grid(row=1, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        self.stats_var = tk.StringVar(value="Loading dashboard stats...")
        tk.Label(
            panel,
            textvariable=self.stats_var,
            bg="#161616",
            fg="#f1f1f1",
            padx=12,
            pady=10,
            anchor="w",
            justify="left",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 10))

        columns = ("id", "name", "goal", "status", "adherence")
        self.members_tree = ttk.Treeview(panel, columns=columns, show="headings", height=15)
        for name, heading, width in (
            ("id", "ID", 60),
            ("name", "Name", 220),
            ("goal", "Goal", 150),
            ("status", "Membership", 120),
            ("adherence", "Adherence", 100),
        ):
            self.members_tree.heading(name, text=heading)
            self.members_tree.column(name, width=width, anchor="center" if name != "name" else "w")

        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.members_tree.yview)
        self.members_tree.configure(yscrollcommand=scrollbar.set)
        self.members_tree.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.members_tree.bind("<<TreeviewSelect>>", self.show_selected_member)

    def _build_detail_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="User Details", padding=14)
        panel.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(14, 0))

        self.detail_text = tk.Text(
            panel,
            height=10,
            bg="#141414",
            fg="#f2f2f2",
            insertbackground="#f2f2f2",
            relief="flat",
            wrap="word",
            font=("Consolas", 11),
        )
        self.detail_text.pack(fill="x")
        self._set_detail_text("Select a user from the table to view full API details.")

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def _set_detail_text(self, message: str) -> None:
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("end", message)
        self.detail_text.configure(state="disabled")

    def test_connection(self) -> None:
        self.api.set_base_url(self.base_url_var.get().strip())
        try:
            health = self.api.health()
        except RuntimeError as exc:
            self.connection_state_var.set(f"Connection failed: {exc}")
            self._set_status("API connection failed")
            messagebox.showerror("Connection Error", str(exc))
            return

        self.connection_state_var.set(f"Connected successfully. API status: {health.get('status', 'unknown')}")
        self._set_status("API connection verified")

    def load_initial_data(self) -> None:
        self.api.set_base_url(self.base_url_var.get().strip())
        try:
            self.program_catalog = self.api.get_programs().get("programs", {})
            self.member_rows = self.api.get_members()
            stats = self.api.get_stats()
        except RuntimeError as exc:
            self.connection_state_var.set(f"Connection failed: {exc}")
            self._set_status("Could not load API data")
            self.goal_box["values"] = ()
            self._populate_members([])
            self.stats_var.set("Dashboard unavailable until the API is reachable.")
            self._set_detail_text(str(exc))
            return

        goal_values = tuple(self.program_catalog.keys())
        self.goal_box["values"] = goal_values
        if goal_values and self.goal_var.get() not in goal_values:
            self.goal_var.set(goal_values[0])
            self.update_goal_hint()

        self._populate_members(self.member_rows)
        self._render_stats(stats)
        self.connection_state_var.set("Connected and data loaded from Flask API.")
        self._set_status("Dashboard refreshed from API")

    def _populate_members(self, members: list[dict]) -> None:
        for row_id in self.members_tree.get_children():
            self.members_tree.delete(row_id)

        for member in members:
            self.members_tree.insert(
                "",
                "end",
                iid=str(member["id"]),
                values=(
                    member["id"],
                    member["name"],
                    member["goal"],
                    member["membership_status"],
                    f'{member["adherence_score"]}%',
                ),
            )

    def _render_stats(self, stats: dict) -> None:
        self.stats_var.set(
            "Total Users: {total_members}    Active Memberships: {active_members}    "
            "Average Adherence: {average_adherence}%    Goals Available: {goals_available}".format(**stats)
        )

    def update_goal_hint(self, event=None) -> None:
        goal = self.goal_var.get()
        if not goal or goal not in self.program_catalog:
            self.goal_hint_var.set("Choose a goal to see the suggested training focus.")
            return

        program = self.program_catalog[goal]
        self.goal_hint_var.set(
            f"{program['name']}\n"
            f"Focus: {program['focus']}\n"
            f"Training Days: {program['days_per_week']} per week"
        )

    def submit_member(self) -> None:
        payload = {
            "name": self.name_var.get().strip(),
            "age": self.age_var.get().strip(),
            "weight_kg": self.weight_var.get().strip(),
            "goal": self.goal_var.get().strip(),
            "adherence_score": self.adherence_var.get().strip(),
            "membership_status": self.membership_var.get().strip(),
        }

        try:
            created = self.api.add_member(payload)
        except RuntimeError as exc:
            self._set_status("User creation failed")
            messagebox.showerror("Add User Failed", str(exc))
            return

        self.clear_form()
        self.load_initial_data()
        self.members_tree.selection_set(str(created["id"]))
        self.members_tree.focus(str(created["id"]))
        self.show_selected_member()
        self._set_status(f"Added user {created['name']} successfully")
        messagebox.showinfo("User Added", f"{created['name']} was added through the Flask API.")

    def clear_form(self) -> None:
        self.name_var.set("")
        self.age_var.set("")
        self.weight_var.set("")
        self.adherence_var.set("80")
        self.membership_var.set("active")
        if self.goal_box["values"]:
            self.goal_var.set(self.goal_box["values"][0])
            self.update_goal_hint()

    def show_selected_member(self, event=None) -> None:
        selected = self.members_tree.selection()
        if not selected:
            return

        member_id = selected[0]
        member = next((row for row in self.member_rows if str(row["id"]) == member_id), None)
        if not member:
            return

        details = [
            f"ID: {member['id']}",
            f"Name: {member['name']}",
            f"Age: {member['age']}",
            f"Weight: {member['weight_kg']} kg",
            f"Goal: {member['goal']}",
            f"Membership: {member['membership_status']}",
            f"Adherence: {member['adherence_score']}%",
            f"Recommended Calories: {member['recommended_calories']} kcal",
            "",
            f"Assigned Program: {member['program']['name']}",
            f"Program Focus: {member['program']['focus']}",
            f"Training Days Per Week: {member['program']['days_per_week']}",
        ]
        self._set_detail_text("\n".join(details))


def main() -> None:
    root = tk.Tk()
    app = ACEestFrontend(root)
    app.clear_form()
    app.update_goal_hint()
    root.mainloop()


if __name__ == "__main__":
    main()
