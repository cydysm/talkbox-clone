(() => {
  const wrapSelection = (field, prefix, suffix = prefix) => {
    const start = field.selectionStart;
    const end = field.selectionEnd;
    const selected = field.value.slice(start, end);
    field.setRangeText(`${prefix}${selected}${suffix}`, start, end, "select");
    field.focus();
    field.dispatchEvent(new Event("input", { bubbles: true }));
  };

  const linePrefix = (field, prefix) => {
    const start = field.selectionStart;
    const lineStart = field.value.lastIndexOf("\n", start - 1) + 1;
    field.setRangeText(prefix, lineStart, lineStart, "end");
    field.setSelectionRange(start + prefix.length, start + prefix.length);
    field.dispatchEvent(new Event("input", { bubbles: true }));
  };

  const insertAtCursor = (field, text) => {
    const start = field.selectionStart;
    field.setRangeText(text, start, field.selectionEnd, "end");
    field.dispatchEvent(new Event("input", { bubbles: true }));
  };

  document.addEventListener("DOMContentLoaded", () => {
    const template = document.getElementById("talkbox-editor-template");
    if (!template) return;

    document.querySelectorAll(".field-content_markdown textarea").forEach((field) => {
      const editor = template.content.firstElementChild.cloneNode(true);
      const fileInput = editor.querySelector("input[type=file]");
      const progress = editor.querySelector("progress");
      field.before(editor);

      editor.addEventListener("click", (event) => {
        const button = event.target.closest("[data-action]");
        if (!button) return;
        const action = button.dataset.action;
        if (action === "bold") wrapSelection(field, "**");
        if (action === "italic") wrapSelection(field, "*");
        if (action === "heading") linePrefix(field, "## ");
        if (action === "quote") linePrefix(field, "> ");
        if (action === "code") wrapSelection(field, "`");
        if (action === "link") wrapSelection(field, "[", "](https://)");
      });

      fileInput.addEventListener("change", async () => {
        if (!fileInput.files.length || !window.confirm(`上传并插入 ${fileInput.files.length} 张图片？`)) return;
        const body = new FormData();
        const postId = document.querySelector("input[name=object_id]");
        if (postId) body.append("post", postId.value);
        Array.from(fileInput.files).forEach((file) => body.append("images", file));
        progress.hidden = false;
        progress.removeAttribute("value");
        try {
          const response = await fetch("/media-api/upload/", { method: "POST", body: body, credentials: "same-origin" });
          const result = await response.json();
          if (!response.ok) throw new Error((result.errors || ["上传失败"]).join("\n"));
          result.images.forEach(({ url }) => insertAtCursor(field, `\n![图片](${url})\n`));
          window.alert(`已插入 ${result.images.length} 张图片。`);
        } catch (error) {
          window.alert(error.message);
        } finally {
          progress.hidden = true;
          fileInput.value = "";
        }
      });
    });
  });
})();
