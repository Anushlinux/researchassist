import curses
import textwrap

from agent import format_steps_text, run_agent


APP_TITLE = "Research Assistant Agent TUI"
HELP_TEXT = "Enter: send | F2: toggle debug pane | F3: clear chat | q: quit"


class ChatTUI:
    def __init__(self):
        self.messages = [
            {
                "role": "assistant",
                "content": (
                    "Ask a research question. Toggle the debug pane with F2 if you want "
                    "to inspect LangChain trace output and tool steps."
                ),
            }
        ]
        self.input_buffer = ""
        self.last_result = None
        self.show_debug = False
        self.chat_scroll = 0
        self.debug_scroll = 0
        self.status = "Ready."

    def run(self, stdscr):
        curses.curs_set(1)
        curses.use_default_colors()
        stdscr.keypad(True)

        while True:
            self.draw(stdscr)
            key = stdscr.getch()

            if key in (ord("q"), ord("Q")):
                break
            if key == curses.KEY_F2:
                self.show_debug = not self.show_debug
                self.debug_scroll = 0
                self.status = "Debug pane enabled." if self.show_debug else "Debug pane hidden."
                continue
            if key == curses.KEY_F3:
                self.messages = []
                self.last_result = None
                self.chat_scroll = 0
                self.debug_scroll = 0
                self.status = "Chat cleared."
                continue
            if key == curses.KEY_UP:
                self.chat_scroll = max(0, self.chat_scroll - 1)
                continue
            if key == curses.KEY_DOWN:
                self.chat_scroll += 1
                continue
            if key == curses.KEY_PPAGE:
                self.debug_scroll = max(0, self.debug_scroll - 5)
                continue
            if key == curses.KEY_NPAGE:
                self.debug_scroll += 5
                continue
            if key in (curses.KEY_ENTER, 10, 13):
                self.submit_query(stdscr)
                continue
            if key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
                continue
            if key == 9:
                self.input_buffer += "    "
                continue
            if 32 <= key <= 126:
                self.input_buffer += chr(key)

    def submit_query(self, stdscr):
        query = self.input_buffer.strip()
        if not query:
            self.status = "Type a question before sending."
            return

        self.messages.append({"role": "user", "content": query})
        self.input_buffer = ""
        self.status = "Running agent..."
        self.draw(stdscr)
        stdscr.refresh()

        result = run_agent(query, capture_debug=self.show_debug)
        self.last_result = result
        self.messages.append({"role": "assistant", "content": result.get("answer", "No answer")})

        if result.get("error"):
            self.status = f"Request failed: {result['error']}"
        else:
            self.status = f"Completed in {result.get('num_steps', 0)} step(s)."

        self.chat_scroll = 10**6
        self.debug_scroll = 0

    def draw(self, stdscr):
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        if width < 80 or height < 24:
            warning = "Resize terminal to at least 80x24."
            stdscr.addnstr(0, 0, warning, max(0, width - 1))
            stdscr.refresh()
            return

        header = f"{APP_TITLE} | {'DEBUG ON' if self.show_debug else 'DEBUG OFF'}"
        stdscr.addnstr(0, 0, header.ljust(width - 1), width - 1, curses.A_REVERSE)

        input_height = 3
        body_top = 1
        body_height = height - input_height - 2

        if self.show_debug:
            chat_width = max(40, int(width * 0.58))
            debug_x = chat_width + 1
            debug_width = width - debug_x
        else:
            chat_width = width
            debug_x = width
            debug_width = 0

        self.draw_chat_pane(stdscr, body_top, 0, body_height, chat_width)
        if self.show_debug and debug_width > 8:
            self.draw_debug_pane(stdscr, body_top, debug_x, body_height, debug_width)

        separator_y = height - input_height - 1
        stdscr.hline(separator_y, 0, ord("-"), width)
        stdscr.addnstr(height - 3, 0, f"Status: {self.status}".ljust(width - 1), width - 1)
        stdscr.addnstr(height - 2, 0, HELP_TEXT.ljust(width - 1), width - 1, curses.A_DIM)
        prompt = "> " + self.input_buffer
        stdscr.addnstr(height - 1, 0, prompt.ljust(width - 1), width - 1)
        cursor_x = min(len(prompt), width - 1)
        stdscr.move(height - 1, cursor_x)
        stdscr.refresh()

    def draw_chat_pane(self, stdscr, y, x, height, width):
        title = " Chat "
        stdscr.addnstr(y, x, title, max(0, width - 1), curses.A_BOLD)
        lines = self.render_chat_lines(max(20, width - 2))
        visible = max(1, height - 1)
        max_scroll = max(0, len(lines) - visible)
        self.chat_scroll = min(self.chat_scroll, max_scroll)
        start = max(0, len(lines) - visible - self.chat_scroll)
        window_lines = lines[start : start + visible]

        for row_offset, line in enumerate(window_lines, start=1):
            stdscr.addnstr(y + row_offset, x, line.ljust(width - 1), width - 1)

    def draw_debug_pane(self, stdscr, y, x, height, width):
        divider_x = x - 1
        for row in range(y, y + height):
            stdscr.addch(row, divider_x, ord("|"))

        stdscr.addnstr(y, x, " Debug ", max(0, width - 1), curses.A_BOLD)
        lines = self.render_debug_lines(max(20, width - 2))
        visible = max(1, height - 1)
        max_scroll = max(0, len(lines) - visible)
        self.debug_scroll = min(self.debug_scroll, max_scroll)
        start = min(self.debug_scroll, max_scroll)
        window_lines = lines[start : start + visible]

        for row_offset, line in enumerate(window_lines, start=1):
            stdscr.addnstr(y + row_offset, x, line.ljust(width - 1), width - 1)

    def render_chat_lines(self, width):
        lines = []
        for message in self.messages:
            prefix = "You: " if message["role"] == "user" else "Agent: "
            wrapped = textwrap.wrap(message["content"], width=max(10, width - len(prefix))) or [""]
            lines.append(prefix + wrapped[0])
            for extra_line in wrapped[1:]:
                lines.append(" " * len(prefix) + extra_line)
            lines.append("")
        return lines or [""]

    def render_debug_lines(self, width):
        if not self.last_result:
            return ["No debug data yet.", "", "Send a query, then toggle F2 to inspect steps and raw LangChain trace."]

        sections = ["Parsed steps:", ""]
        steps_text = format_steps_text(self.last_result)
        for line in steps_text.splitlines():
            sections.extend(textwrap.wrap(line, width=max(10, width)) or [""])

        raw_trace = self.last_result.get("debug_trace", "").strip()
        sections.extend(["", "Raw LangChain debug:", ""])
        if raw_trace:
            for line in raw_trace.splitlines():
                sections.extend(textwrap.wrap(line, width=max(10, width)) or [""])
        else:
            sections.append("Debug capture was off for this query. Toggle F2 before sending the next one.")
        return sections


def main():
    curses.wrapper(ChatTUI().run)


if __name__ == "__main__":
    main()
