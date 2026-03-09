/* tslint:disable */
/* eslint-disable */

export class AquariumSim {
    free(): void;
    [Symbol.dispose](): void;
    fish_count(): number;
    constructor(width: number, height: number, fish_count: number, seed: number);
    set_role(index: number, role: number): void;
    set_speed_factor(index: number, factor: number): void;
    snapshot(): Float32Array;
    step(dt: number, width: number, height: number): void;
}

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly __wbg_aquariumsim_free: (a: number, b: number) => void;
    readonly aquariumsim_fish_count: (a: number) => number;
    readonly aquariumsim_new: (a: number, b: number, c: number, d: number) => number;
    readonly aquariumsim_set_role: (a: number, b: number, c: number) => void;
    readonly aquariumsim_set_speed_factor: (a: number, b: number, c: number) => void;
    readonly aquariumsim_snapshot: (a: number) => [number, number];
    readonly aquariumsim_step: (a: number, b: number, c: number, d: number) => void;
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
 * Instantiates the given `module`, which can either be bytes or
 * a precompiled `WebAssembly.Module`.
 *
 * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
 *
 * @returns {InitOutput}
 */
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
