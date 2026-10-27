# BH four-observation audit

Written by the root agent from the independent read-only rt_block_sampler_review audit and retained artifacts. All four runs pass exact wrapper/native/root-envelope/raw/result binding and cleanup checks.

| Run | Native monotonic seconds | Result | RT stop/fault/gate | Physical annotation | Selected late context |
| --- | --- | --- | --- | --- | --- |
| pre-x | 156739.424746–156739.438211 | AlreadyFaulted | 1 / 0x1001 / 0 | Owner reports black | Shared mode4/6 action bucket 7; mode1 history/aggregate zero |
| post-x | 157157.160342–157177.164244 | 80 clean cycles | 0 / 0 / 1 | Screensaver visible; owner confirms still visible | Mode1 candidate limit200, aggregate0; alternate selector0 |
| for-you-x | 157270.250946–157290.254719 | 80 clean cycles | 0 / 0 / 1 | Keypress not proved inside this capture | Same R/C/H/L final bytes as post-x; no onset |
| after-for-you-x | 157360.898267–157360.911911 | AlreadyFaulted | 1 / 0x1001 / 0 | Owner saw For You about1s, then black | Mode1 history[4,0,4,0], aggregate44, alternate limit40, mode1 action bucket7 |

Each run has24 authenticated root calls, one native invocation, no parameter writes or retries, known ReadyForHeader terminal phase, successful release/close and STAGE_ABSENT. Faulted runs have6 fixed reads/12 exact bulks. Clean runs have480 reads/960 bulks; only the final cycle retains raw windows and79 previous cycles have summary evidence. R/M/C/H/L/R reads are sequential, not atomic.

The For You-labelled20s observer ended clean. Physical keypress time is not bounded inside its native interval; the later faulted read starts70.64s after that interval ends. Therefore no first-fault/onset or event tuple was captured. The late44>40 comparison is numerically consistent with one reconstructed mode1 branch, not an event-time comparison. The initial faulted run instead has a shared mode4/6 action bucket7 and zero mode1 history. Neither action mark uniquely establishes a faulting mode.

All four runs use unchanged wrapper manifest915d19e20d7e5e7fc81a1962cec150ef17f2d00229277666918d199e755d2fe1 and native manifest44f74a8a695f41ed21d68a7a36e13934eebc74050bf991c634e6015ec88043a2. Software result physical flags remain false; owner observations are separate records.

| Run | Artifact | SHA-256 |
| --- | --- | --- |
| pre-x | record.json | `7d3486bcef83297738fbe4e4822460ccfa79bbcce70e0415a015045fe7e570b1` |
| pre-x | result.json | `c7582e97384efaf2c6bd0895aa9b9ecbee8d5a78c13f1850bbe40124ef2c6e32` |
| pre-x | native.stdout.bin | `5e31491f0fa5ddef56eeb30b1d1d566157c1d45a88c4d1ea8c1d0483d4f64be7` |
| post-x | record.json | `4fa052c281ee90d5c08e641a0364b9a00f8775743445c7df4c787eefeeb207b5` |
| post-x | result.json | `bbb882baa76b8e5793f828d95b5f6eab1d92345ece7ff99866a54625672c2bce` |
| post-x | native.stdout.bin | `011e5187162bfefd022388a72c72fd36ae49bb91b23193f8e6a74bda59f27c4a` |
| for-you-x | record.json | `181c04b4a0af3708231a5b5989a18ae25449cd6d54c0b239f57b854e54530d48` |
| for-you-x | result.json | `af7ac60c7ae118f1b0a4344fcf60393c17df1bd945443c8bac246adcfa4a7786` |
| for-you-x | native.stdout.bin | `52318b456a920e4f117202572b5c10b1927e7d211ed2a0d255aecd86ef61b3b7` |
| after-for-you-x | record.json | `832e214e4e458b61a12663ba1ae3fea7462563db41eaba25ac39be2d305869d6` |
| after-for-you-x | result.json | `7580b9994ec99da4508ef9d74d9e984ad9e80106cc08f8624de36a366a2b47ca` |
| after-for-you-x | native.stdout.bin | `fc1a83d052f8680b6255a8fe8683778b2a141dca011f5348554fcd6975ed0f6b` |
