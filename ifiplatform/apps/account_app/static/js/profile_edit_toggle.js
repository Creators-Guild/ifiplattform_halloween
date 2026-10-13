document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".field-edit-toggle").forEach((button) => {
    const field = document.getElementById(button.dataset.target);
    if (!field) {
      return;
    }
    const saveButton = button.parentElement.querySelector(".field-save-btn");

    const editText = button.dataset.editText || button.textContent;
    const cancelText = button.dataset.cancelText || "Cancel";
    // field.value reflects the live input as it's typed; defaultValue
    // stays pinned to the value attribute the server rendered, so it's
    // what "cancel" restores regardless of what got typed in the meantime.
    const originalValue = field.defaultValue;

    button.addEventListener("click", () => {
      const editing = field.readOnly;
      field.readOnly = !editing;
      field.classList.toggle("field-locked", !editing);
      button.textContent = editing ? cancelText : editText;
      if (saveButton) {
        saveButton.hidden = !editing;
      }

      if (editing) {
        field.focus();
      } else {
        field.value = originalValue;
      }
    });
  });
});
