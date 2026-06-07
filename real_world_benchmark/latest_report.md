# Real World Benchmark Report

- Generated at: `2026-03-22 21:49:59`
- Manifest: [literature_cases.json](D:/cursorku/real_world_benchmark/literature_cases.json)

## Selector Accuracy

| Strategy | Accuracy | Test Samples |
| --- | ---: | ---: |
| static_rf | 1.000 | 60 |
| mlp_nn | 1.000 | 60 |
| gnn_selector | 1.000 | 60 |
| dynamic_rl | 0.267 | 60 |

## Local Runnable Cases

### heat1d_rod_cooling

- Equation: `heat1d`
- Application: 1D heat conduction in a rod / diffusion-like transport analogue
- Best by error: `spectral`
- Best by time: `pinn`
- Best balanced: `spectral`

| Algorithm | L2 Error | Linf Error | Elapsed (s) |
| --- | ---: | ---: | ---: |
| fdm | 1.743408e-05 | 2.492453e-05 | 0.108959 |
| fvm | 3.487575e-05 | 4.956775e-05 | 0.019377 |
| fem | 1.743429e-05 | 2.484311e-05 | 0.347539 |
| spectral | 9.427012e-12 | 1.339862e-11 | 0.591239 |
| pinn | 3.053863e-05 | 4.882831e-05 | 0.000000 |

### poisson1d_steady_diffusion

- Equation: `poisson1d`
- Application: 1D steady diffusion / source-driven potential field
- Best by error: `spectral`
- Best by time: `bem`
- Best balanced: `spectral`

| Algorithm | L2 Error | Linf Error | Elapsed (s) |
| --- | ---: | ---: | ---: |
| fdm | 5.787143e-05 | 8.225076e-05 | 0.000375 |
| fem | 5.786572e-05 | 8.224264e-05 | 0.000567 |
| spectral | 1.279422e-16 | 2.914335e-16 | 0.000033 |
| bem | 5.787143e-05 | 8.225076e-05 | 0.000013 |

### wave1d_string_vibration

- Equation: `wave1d`
- Application: 1D vibrating string benchmark
- Best by error: `spectral`
- Best by time: `spectral`
- Best balanced: `spectral`

| Algorithm | L2 Error | Linf Error | Elapsed (s) |
| --- | ---: | ---: | ---: |
| fdm | 4.260903e-05 | 6.055881e-05 | 0.002664 |
| fem | 3.897708e-05 | 5.694143e-05 | 0.002520 |
| spectral | 9.215974e-17 | 1.953375e-16 | 0.000162 |

### heat2d_square_plate

- Equation: `heat2d`
- Application: 2D square plate conduction benchmark
- Best by error: `fdm`
- Best by time: `fvm`
- Best balanced: `fvm`

| Algorithm | L2 Error | Linf Error | Elapsed (s) |
| --- | ---: | ---: | ---: |
| fdm | 1.846874e-04 | 3.786093e-04 | 0.013534 |
| fvm | 1.846874e-04 | 3.786093e-04 | 0.011274 |
| fem | 2.801501e-04 | 5.673644e-04 | 1.403073 |

### wave2d_membrane

- Equation: `wave2d`
- Application: 2D membrane / shallow-water-like wave propagation analogue
- Best by error: `spectral`
- Best by time: `fdm`
- Best balanced: `spectral`

| Algorithm | L2 Error | Linf Error | Elapsed (s) |
| --- | ---: | ---: | ---: |
| fdm | 9.612950e-06 | 1.970655e-05 | 0.000471 |
| fem | 8.068292e-05 | 1.636414e-04 | 0.009365 |
| spectral | 1.201835e-16 | 5.551115e-16 | 0.000521 |

### heat3d_cube_conduction

- Equation: `heat3d`
- Application: 3D cube conduction benchmark
- Best by error: `fvm`
- Best by time: `fvm`
- Best balanced: `fvm`

| Algorithm | L2 Error | Linf Error | Elapsed (s) |
| --- | ---: | ---: | ---: |
| fdm | 1.687496e-03 | 5.506514e-03 | 0.000792 |
| fvm | 1.687496e-03 | 5.506514e-03 | 0.000757 |
| fem | 4.332559e-03 | 1.363083e-02 | 0.002900 |

### wave3d_cavity_vibration

- Equation: `wave3d`
- Application: 3D cavity/acoustic-wave benchmark
- Best by error: `spectral`
- Best by time: `fem`
- Best balanced: `fdm`

| Algorithm | L2 Error | Linf Error | Elapsed (s) |
| --- | ---: | ---: | ---: |
| fdm | 6.913048e-05 | 2.168500e-04 | 0.000299 |
| fem | 1.796616e-03 | 5.092353e-03 | 0.000121 |
| spectral | 1.788207e-16 | 7.494005e-16 | 0.000364 |

### poisson3d_electrostatic_box

- Equation: `poisson3d`
- Application: 3D electrostatic / Darcy-like elliptic benchmark
- Best by error: `fdm`
- Best by time: `fdm`
- Best balanced: `fdm`

| Algorithm | L2 Error | Linf Error | Elapsed (s) |
| --- | ---: | ---: | ---: |
| fdm | 1.341118e-03 | 4.206847e-03 | 0.021604 |
| fem | 6.676829e-03 | 2.065667e-02 | 0.024873 |
| bem | 1.384151e+00 | 1.877598e+00 | 0.415674 |

## External Baseline Comparison

### heat1d_rod_cooling

| Type | Name | L2 Error | Linf Error | Elapsed (s) | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| local | fdm | 1.743408e-05 | 2.492453e-05 | 0.108959 | local_heat1d |
| local | fvm | 3.487575e-05 | 4.956775e-05 | 0.019377 | local_heat1d |
| local | fem | 1.743429e-05 | 2.484311e-05 | 0.347539 | local_heat1d |
| local | spectral | 9.427012e-12 | 1.339862e-11 | 0.591239 | local_heat1d |
| local | pinn | 3.053863e-05 | 4.882831e-05 | 0.000000 | local_heat1d |
| external | FNO | 2.300000e-02 | N/A | 0.120000 | Takamoto et al., NeurIPS 2022, Table 1 |
| external | U-Net | 3.100000e-02 | N/A | 0.080000 | Takamoto et al., NeurIPS 2022, Table 1 |
| external | PINN | 8.900000e-02 | N/A | 45.000000 | Takamoto et al., NeurIPS 2022, Table 1 |

### poisson1d_steady_diffusion

| Type | Name | L2 Error | Linf Error | Elapsed (s) | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| local | fdm | 5.787143e-05 | 8.225076e-05 | 0.000375 | local_poisson1d |
| local | fem | 5.786572e-05 | 8.224264e-05 | 0.000567 | local_poisson1d |
| local | spectral | 1.279422e-16 | 2.914335e-16 | 0.000033 | local_poisson1d |
| local | bem | 5.787143e-05 | 8.225076e-05 | 0.000013 | local_poisson1d |

### wave1d_string_vibration

| Type | Name | L2 Error | Linf Error | Elapsed (s) | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| local | fdm | 4.260903e-05 | 6.055881e-05 | 0.002664 | local_wave1d |
| local | fem | 3.897708e-05 | 5.694143e-05 | 0.002520 | local_wave1d |
| local | spectral | 9.215974e-17 | 1.953375e-16 | 0.000162 | local_wave1d |
| external | FNO | 1.800000e-02 | N/A | 0.100000 | Takamoto et al., NeurIPS 2022, Table 1 |
| external | U-Net | 2.500000e-02 | N/A | 0.070000 | Takamoto et al., NeurIPS 2022, Table 1 |

### heat2d_square_plate

| Type | Name | L2 Error | Linf Error | Elapsed (s) | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| local | fdm | 1.846874e-04 | 3.786093e-04 | 0.013534 | local_heat2d |
| local | fvm | 1.846874e-04 | 3.786093e-04 | 0.011274 | local_heat2d |
| local | fem | 2.801501e-04 | 5.673644e-04 | 1.403073 | local_heat2d |
| external | FNO | 1.500000e-02 | N/A | 0.350000 | Takamoto et al., NeurIPS 2022, Table 2 |
| external | U-Net | 2.100000e-02 | N/A | 0.250000 | Takamoto et al., NeurIPS 2022, Table 2 |

### wave2d_membrane

| Type | Name | L2 Error | Linf Error | Elapsed (s) | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| local | fdm | 9.612950e-06 | 1.970655e-05 | 0.000471 | local_wave2d |
| local | fem | 8.068292e-05 | 1.636414e-04 | 0.009365 | local_wave2d |
| local | spectral | 1.201835e-16 | 5.551115e-16 | 0.000521 | local_wave2d |
| external | FNO | 3.200000e-02 | N/A | 0.450000 | Takamoto et al., NeurIPS 2022, Table 2 |
| external | U-Net | 4.500000e-02 | N/A | 0.300000 | Takamoto et al., NeurIPS 2022, Table 2 |

### heat3d_cube_conduction

| Type | Name | L2 Error | Linf Error | Elapsed (s) | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| local | fdm | 1.687496e-03 | 5.506514e-03 | 0.000792 | local_heat3d |
| local | fvm | 1.687496e-03 | 5.506514e-03 | 0.000757 | local_heat3d |
| local | fem | 4.332559e-03 | 1.363083e-02 | 0.002900 | local_heat3d |
| external | FNO | 4.100000e-02 | N/A | 2.500000 | Takamoto et al., NeurIPS 2022, Table 3 |
| external | U-Net | 5.800000e-02 | N/A | 1.800000 | Takamoto et al., NeurIPS 2022, Table 3 |

### wave3d_cavity_vibration

| Type | Name | L2 Error | Linf Error | Elapsed (s) | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| local | fdm | 6.913048e-05 | 2.168500e-04 | 0.000299 | local_wave3d |
| local | fem | 1.796616e-03 | 5.092353e-03 | 0.000121 | local_wave3d |
| local | spectral | 1.788207e-16 | 7.494005e-16 | 0.000364 | local_wave3d |

### poisson3d_electrostatic_box

| Type | Name | L2 Error | Linf Error | Elapsed (s) | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| local | fdm | 1.341118e-03 | 4.206847e-03 | 0.021604 | local_poisson3d |
| local | fem | 6.676829e-03 | 2.065667e-02 | 0.024873 | local_poisson3d |
| local | bem | 1.384151e+00 | 1.877598e+00 | 0.415674 | local_poisson3d |
| external | FNO | 2.800000e-02 | N/A | 0.400000 | Takamoto et al., NeurIPS 2022, Table 2 |
| external | U-Net | 3.500000e-02 | N/A | 0.280000 | Takamoto et al., NeurIPS 2022, Table 2 |

