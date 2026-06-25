export function createElement(tagName, { className, text, attributes = {} } = {}) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;

  Object.entries(attributes).forEach(([name, value]) => {
    if (value !== false && value !== null && value !== undefined) {
      element.setAttribute(name, String(value));
    }
  });
  return element;
}
