use wasm_bindgen::prelude::*;

const PINK_OCTAVES: usize = 8;
const TAU: f32 = std::f32::consts::TAU;

#[wasm_bindgen]
pub struct AquariumSim {
    fishes: Vec<Fish>,
    rng: Rng,
}

#[derive(Clone)]
struct Fish {
    x: f32,
    y: f32,
    vx: f32,
    vy: f32,
    speed: f32,
    depth: f32,
    turn_bias: f32,
    change_timer: f32,
    burst_timer: f32,
    role: u8,
    speed_factor: f32,
    noise: PinkNoise,
}

#[derive(Clone)]
struct PinkNoise {
    values: [f32; PINK_OCTAVES],
    counter: u32,
}

struct Rng {
    state: u64,
}

impl Rng {
    fn new(seed: u64) -> Self {
        let init = if seed == 0 {
            0x9E37_79B9_7F4A_7C15
        } else {
            seed
        };
        Self { state: init }
    }

    fn next_u32(&mut self) -> u32 {
        let mut x = self.state;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.state = x;
        ((x.wrapping_mul(0x2545_F491_4F6C_DD1D)) >> 32) as u32
    }

    fn next_f32(&mut self) -> f32 {
        self.next_u32() as f32 / u32::MAX as f32
    }

    fn range(&mut self, min: f32, max: f32) -> f32 {
        min + (max - min) * self.next_f32()
    }
}

impl PinkNoise {
    fn new(rng: &mut Rng) -> Self {
        let mut values = [0.0; PINK_OCTAVES];
        for value in &mut values {
            *value = rng.range(-1.0, 1.0);
        }
        Self { values, counter: 0 }
    }

    fn next(&mut self, rng: &mut Rng) -> f32 {
        self.counter = self.counter.wrapping_add(1);
        let idx = (self.counter.trailing_zeros() as usize).min(PINK_OCTAVES - 1);
        self.values[idx] = rng.range(-1.0, 1.0);

        let mut sum = 0.0;
        for value in self.values {
            sum += value;
        }
        sum / PINK_OCTAVES as f32
    }
}

#[wasm_bindgen]
impl AquariumSim {
    #[wasm_bindgen(constructor)]
    pub fn new(width: f32, height: f32, fish_count: usize, seed: u32) -> Self {
        let mut rng = Rng::new(seed as u64);
        let mut fishes = Vec::with_capacity(fish_count);

        for _ in 0..fish_count {
            let heading = rng.range(0.0, TAU);
            let speed = rng.range(12.0, 30.0);
            let depth = rng.range(0.0, 1.0);
            fishes.push(Fish {
                x: rng.range(40.0, (width - 40.0).max(40.0)),
                y: rng.range(40.0, (height - 40.0).max(40.0)),
                vx: heading.cos() * speed,
                vy: heading.sin() * speed,
                speed,
                depth,
                turn_bias: rng.range(-0.7, 0.7),
                change_timer: rng.range(2.0, 8.0),
                burst_timer: 0.0,
                role: 0,
                speed_factor: 1.0,
                noise: PinkNoise::new(&mut rng),
            });
        }

        Self { fishes, rng }
    }

    pub fn fish_count(&self) -> usize {
        self.fishes.len()
    }

    pub fn set_role(&mut self, index: usize, role: u8) {
        if let Some(fish) = self.fishes.get_mut(index) {
            fish.role = role;
        }
    }

    pub fn set_speed_factor(&mut self, index: usize, factor: f32) {
        if let Some(fish) = self.fishes.get_mut(index) {
            fish.speed_factor = factor.clamp(0.2, 4.0);
        }
    }

    pub fn step(&mut self, dt: f32, width: f32, height: f32) {
        let dt = dt.clamp(0.001, 0.05);
        let w = width.max(120.0);
        let h = height.max(120.0);
        let margin = 28.0;

        for fish in &mut self.fishes {
            fish.change_timer -= dt;
            if fish.change_timer <= 0.0 {
                fish.change_timer = self.rng.range(3.0, 10.0);
                fish.turn_bias = self.rng.range(-1.0, 1.0) * 0.9;
                fish.speed = (fish.speed + self.rng.range(-2.0, 2.0)).clamp(10.0, 34.0);
            }

            if fish.burst_timer <= 0.0 && self.rng.next_f32() < dt * 0.015 {
                fish.burst_timer = self.rng.range(0.7, 1.8);
            }
            fish.burst_timer = (fish.burst_timer - dt).max(0.0);

            let pink = fish.noise.next(&mut self.rng);
            let heading = fish.vy.atan2(fish.vx);
            let (speed_mul, turn_mul, vertical_mul) = match fish.role {
                1 => (1.9, 0.58, 0.85),  // shark-like: faster and steadier
                2 => (0.82, 0.72, 0.62), // ray-like: slower and flatter
                _ => (1.0, 0.9, 1.0),
            };
            let turn = pink * turn_mul + fish.turn_bias * 0.28;
            let target_heading = heading + turn * dt;

            let burst_mul = if fish.burst_timer > 0.0 { 1.4 } else { 1.0 };
            let depth_mul = 0.85 + fish.depth * 0.5;
            let target_speed = fish.speed * depth_mul * burst_mul * speed_mul * fish.speed_factor;

            let desired_vx = target_heading.cos() * target_speed;
            let desired_vy =
                target_heading.sin() * target_speed * (0.72 + fish.depth * 0.25) * vertical_mul;

            fish.vx = fish.vx * 0.965 + desired_vx * 0.035;
            fish.vy = fish.vy * 0.96 + desired_vy * 0.04;

            fish.x += fish.vx * dt;
            fish.y += fish.vy * dt;

            if fish.x < margin {
                fish.x = margin;
                fish.vx = fish.vx.abs();
                fish.turn_bias = self.rng.range(-0.2, 0.8);
            } else if fish.x > w - margin {
                fish.x = w - margin;
                fish.vx = -fish.vx.abs();
                fish.turn_bias = self.rng.range(-0.8, 0.2);
            }

            if fish.y < margin {
                fish.y = margin;
                fish.vy = fish.vy.abs() * 0.6;
                fish.turn_bias *= 0.5;
            } else if fish.y > h - margin {
                fish.y = h - margin;
                fish.vy = -fish.vy.abs() * 0.6;
                fish.turn_bias *= 0.5;
            }
        }
    }

    pub fn snapshot(&self) -> Box<[f32]> {
        let mut out = Vec::with_capacity(self.fishes.len() * 5);
        for fish in &self.fishes {
            let dir = if fish.vx >= 0.0 { 1.0 } else { -1.0 };
            let scale = 0.65 + fish.depth * 0.55;
            out.push(fish.x);
            out.push(fish.y);
            out.push(dir);
            out.push(scale);
            out.push(fish.depth);
        }
        out.into_boxed_slice()
    }
}
