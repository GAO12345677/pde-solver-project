# Statistical Benchmark Report (100 Runs)

- Generated at: `2026-03-22 22:26:25`
- Runs per case: `100`
- Total solver calls: `800`
- Total elapsed time: `882.09s`

## heat1d_rod_cooling

- Equation: `heat1d`
- Application: 1D heat conduction in a rod / diffusion-like transport analogue
- Best by mean error: `spectral`
- Best by mean time: `pinn`

| Algorithm | L2 Mean | L2 Std | L2 95% CI | Time Mean (s) | Time Std |
| --- | ---: | ---: | ---: | ---: | ---: |
| fdm | 1.743408e-05 | 6.810401e-21 | [1.74e-05, 1.74e-05] | 0.098251 | 0.008451 |
| fvm | 3.487575e-05 | 1.362080e-20 | [3.49e-05, 3.49e-05] | 0.018968 | 0.002261 |
| fem | 1.743429e-05 | 0.000000e+00 | [1.74e-05, 1.74e-05] | 0.355810 | 0.021481 |
| spectral | 9.427012e-12 | 0.000000e+00 | [9.43e-12, 9.43e-12] | 0.520728 | 0.027507 |
| pinn | 3.053863e-05 | 6.810401e-21 | [3.05e-05, 3.05e-05] | 0.000000 | 0.000000 |

## poisson1d_steady_diffusion

- Equation: `poisson1d`
- Application: 1D steady diffusion / source-driven potential field
- Best by mean error: `spectral`
- Best by mean time: `bem`

| Algorithm | L2 Mean | L2 Std | L2 95% CI | Time Mean (s) | Time Std |
| --- | ---: | ---: | ---: | ---: | ---: |
| fdm | 5.787143e-05 | 6.810401e-21 | [5.79e-05, 5.79e-05] | 0.000248 | 0.000241 |
| fem | 5.786572e-05 | 6.810401e-21 | [5.79e-05, 5.79e-05] | 0.000221 | 0.000212 |
| spectral | 1.279422e-16 | 2.477610e-32 | [1.28e-16, 1.28e-16] | 0.000037 | 0.000033 |
| bem | 5.787143e-05 | 2.043120e-20 | [5.79e-05, 5.79e-05] | 0.000013 | 0.000009 |

## wave1d_string_vibration

- Equation: `wave1d`
- Application: 1D vibrating string benchmark
- Best by mean error: `spectral`
- Best by mean time: `spectral`

| Algorithm | L2 Mean | L2 Std | L2 95% CI | Time Mean (s) | Time Std |
| --- | ---: | ---: | ---: | ---: | ---: |
| fdm | 4.260903e-05 | 1.362080e-20 | [4.26e-05, 4.26e-05] | 0.002942 | 0.000828 |
| fem | 3.897708e-05 | 0.000000e+00 | [3.90e-05, 3.90e-05] | 0.002913 | 0.000587 |
| spectral | 9.215974e-17 | 2.477610e-32 | [9.22e-17, 9.22e-17] | 0.000174 | 0.000118 |

## heat2d_square_plate

- Equation: `heat2d`
- Application: 2D square plate conduction benchmark
- Best by mean error: `fdm`
- Best by mean time: `fdm`

| Algorithm | L2 Mean | L2 Std | L2 95% CI | Time Mean (s) | Time Std |
| --- | ---: | ---: | ---: | ---: | ---: |
| fdm | 1.846874e-04 | 2.724160e-20 | [1.85e-04, 1.85e-04] | 0.014959 | 0.004471 |
| fvm | 1.846874e-04 | 5.448321e-20 | [1.85e-04, 1.85e-04] | 0.015957 | 0.002628 |
| fem | 2.801501e-04 | 5.448321e-20 | [2.80e-04, 2.80e-04] | 1.388928 | 0.150602 |

## wave2d_membrane

- Equation: `wave2d`
- Application: 2D membrane / shallow-water-like wave propagation analogue
- Best by mean error: `spectral`
- Best by mean time: `spectral`

| Algorithm | L2 Mean | L2 Std | L2 95% CI | Time Mean (s) | Time Std |
| --- | ---: | ---: | ---: | ---: | ---: |
| fdm | 9.612950e-06 | 3.405201e-21 | [9.61e-06, 9.61e-06] | 0.000474 | 0.000062 |
| fem | 8.068292e-05 | 1.362080e-20 | [8.07e-05, 8.07e-05] | 0.005177 | 0.001453 |
| spectral | 1.201835e-16 | 2.477610e-32 | [1.20e-16, 1.20e-16] | 0.000247 | 0.000062 |

## heat3d_cube_conduction

- Equation: `heat3d`
- Application: 3D cube conduction benchmark
- Best by mean error: `fvm`
- Best by mean time: `fdm`

| Algorithm | L2 Mean | L2 Std | L2 95% CI | Time Mean (s) | Time Std |
| --- | ---: | ---: | ---: | ---: | ---: |
| fdm | 1.687496e-03 | 4.358657e-19 | [1.69e-03, 1.69e-03] | 0.000743 | 0.000145 |
| fvm | 1.687496e-03 | 4.358657e-19 | [1.69e-03, 1.69e-03] | 0.000796 | 0.000227 |
| fem | 4.332559e-03 | 8.717313e-19 | [4.33e-03, 4.33e-03] | 0.002036 | 0.000754 |

## wave3d_cavity_vibration

- Equation: `wave3d`
- Application: 3D cavity/acoustic-wave benchmark
- Best by mean error: `spectral`
- Best by mean time: `fem`

| Algorithm | L2 Mean | L2 Std | L2 95% CI | Time Mean (s) | Time Std |
| --- | ---: | ---: | ---: | ---: | ---: |
| fdm | 6.913048e-05 | 0.000000e+00 | [6.91e-05, 6.91e-05] | 0.000327 | 0.000220 |
| fem | 1.796616e-03 | 2.179328e-19 | [1.80e-03, 1.80e-03] | 0.000170 | 0.000135 |
| spectral | 1.788207e-16 | 7.432829e-32 | [1.79e-16, 1.79e-16] | 0.000451 | 0.000287 |

## poisson3d_electrostatic_box

- Equation: `poisson3d`
- Application: 3D electrostatic / Darcy-like elliptic benchmark
- Best by mean error: `fdm`
- Best by mean time: `fem`

| Algorithm | L2 Mean | L2 Std | L2 95% CI | Time Mean (s) | Time Std |
| --- | ---: | ---: | ---: | ---: | ---: |
| fdm | 1.341118e-03 | 6.537985e-19 | [1.34e-03, 1.34e-03] | 0.025571 | 0.004205 |
| fem | 6.676829e-03 | 1.743463e-18 | [6.68e-03, 6.68e-03] | 0.025016 | 0.002799 |
| bem | 1.384151e+00 | 4.463264e-16 | [1.38e+00, 1.38e+00] | 0.449180 | 0.027543 |

