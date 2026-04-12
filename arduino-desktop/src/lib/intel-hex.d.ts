declare module 'intel-hex' {
  export function parseIntelHex(data: string): Record<string, number>;
  export function formatIntelHex(data: Record<string, number>): string;
}
