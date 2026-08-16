// Place any global data in this file.
// You can import this data from anywhere in your site by using the `import` keyword.

export const SITE_TITLE = 'Matrix';
export const SITE_DESCRIPTION = 'Welcome to my website!';

// Ask AI widget endpoint; override at build time via PUBLIC_CHAT_ENDPOINT.
export const CHAT_ENDPOINT = import.meta.env.PUBLIC_CHAT_ENDPOINT ?? '/chat';
export const CHAT_MODEL = 'nvidia/nemotron-3.5-lightning-30b-a3b';
export const CHAT_MAX_TOKENS = 16384;
export const CHAT_TEMPERATURE = 1;
export const CHAT_TOP_P = 0.95;
