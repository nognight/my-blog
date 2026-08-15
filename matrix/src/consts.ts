// Place any global data in this file.
// You can import this data from anywhere in your site by using the `import` keyword.

export const SITE_TITLE = 'Matrix';
export const SITE_DESCRIPTION = 'Welcome to my website!';

// Ask AI widget endpoint; override at build time via PUBLIC_CHAT_ENDPOINT.
export const CHAT_ENDPOINT = import.meta.env.PUBLIC_CHAT_ENDPOINT ?? '/chat';
export const CHAT_MODEL = 'nvidia/llama-3.1-nemotron-nano-8b-v1';
export const CHAT_MAX_TOKENS = 512;
export const CHAT_TEMPERATURE = 0.7;
