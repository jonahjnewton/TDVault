---
layout: post
title: RenderMan - Set Threads on denoise_batch
description: Pixar's RenderMan 25+ denoise_batch does not provide an arg to set the number of threads when denoising images. However, there is a workaround.
---
## The Problem - Setting threads for RenderMan's denoise_batch executable
Pixar's RenderMan 25+ [denoise_batch](https://rmanwiki-26.pixar.com/space/REN26/19661811/Denoiser+Command+Line) executable unfortunately does not provide an argument to set the number of threads to use when denoising images, and as such, it uses all available CPU threads on the computer it runs on. This makes it very hard to manage `denoise_batch` jobs on a render farm without setting aside specific machines/blades specifically for denoising, especially on Linux. However, there is a workaround.

Setting the `OMP_NUM_THREADS` environment variable [allows us to tell OpenMP](https://www.openmp.org/spec-html/5.0/openmpse50.html) (the multiprocessing library used by `denoise_batch`) how many threads to use.

## Examples - RenderMan denoise_batch Threads
The following examples will set `OMP_NUM_THREADS` to 12 on different platforms, telling the denoiser to use 12 threads. You can substitute 12 with any integer.
### Windows
```
set OMP_NUM_THREADS=12
denoise_batch [args]
```
### Linux/macOS
```
export OMP_NUM_THREADS=12
denoise_batch [args]
```

Whether you're going for photorealistic RenderMan renders or stylised looks, the denoiser is world-class for cleaning up renders and is used in studios all over the world. I hope this tutorial helps individual users and studios alike utilise the RenderMan denoiser at scale.