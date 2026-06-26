export function createElement(tagName, options = {}) {
  const element = document.createElement(tagName);
  const { className, text, attributes = {}, dataset = {}, children = [], on = {} } = options;

  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;

  for (const [name, value] of Object.entries(attributes)) {
    if (value !== undefined && value !== null) element.setAttribute(name, String(value));
  }
  for (const [name, value] of Object.entries(dataset)) element.dataset[name] = String(value);
  for (const [eventName, listener] of Object.entries(on)) {
    element.addEventListener(eventName, listener);
  }

  element.append(...children.filter(Boolean));
  return element;
}
