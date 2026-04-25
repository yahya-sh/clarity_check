const notyf = new Notyf({
  duration: 4000,
  position: { x: "right", y: "top" },
  dismissible: true,
  types: [
    {
      type: 'info',
      className: 'notyf__toast--info',
      icon: '<svg xmlns="http://w3.org" width="24" height="24" viewBox="0 0 24 24" fill="white"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>'
    }
  ]
});

const messages = window.FLASH_MESSAGES || [];

messages.forEach(([category, message]) => {
  if (category === "success") {
    notyf.success(message);
  } else if (category === "error") {
    notyf.error(message);
  } else if (category === "info") {
    notyf.open({
      type: "info",
      message: message
    });
  } else {
    notyf.open({ message });
  }
});