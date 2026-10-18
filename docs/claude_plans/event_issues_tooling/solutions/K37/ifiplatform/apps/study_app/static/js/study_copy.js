// "Copy this excuse" on the study page: puts the joke on the clipboard, to
// paste in a group chat. Reads the joke when clicked, since another issue
// can swap it without a reload.
document.addEventListener("DOMContentLoaded", () => {
  const joke = document.getElementById("study-joke");
  const tools = document.getElementById("study-joke-tools");
  if (!joke || !tools) {
    return;
  }
  const button = document.createElement("button");
  button.type = "button";
  button.className = "joke-copy";
  const label = "📋 Copy this excuse";
  button.textContent = label;
  let timer = null;

  function say(text) {
    button.textContent = text;
    clearTimeout(timer);
    timer = setTimeout(() => {
      button.textContent = label;
    }, 2000);
  }

  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(joke.textContent.trim());
      say("✅ Copied!");
    } catch (error) {
      say("Couldn't copy: select the text instead");
    }
  });
  tools.append(button);
});
