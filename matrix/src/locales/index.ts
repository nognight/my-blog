import en from './en.json';
import ja from './ja.json';
import zh from './zh.json';

export const locales = {
	en,
	ja,
	zh,
} as const;

export type LocaleKey = keyof typeof locales;
export type LocaleStrings = (typeof locales)[LocaleKey];

export function isSupportedLocale(
	value: string | null | undefined,
): value is LocaleKey {
	return value !== null && value !== undefined && value in locales;
}

export function getLocale(value: string | null | undefined): LocaleKey {
	return isSupportedLocale(value) ? value : 'en';
}