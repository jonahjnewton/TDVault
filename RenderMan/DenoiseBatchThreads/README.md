---
layout: post
title: Setting Threads on RenderMan 25+ denoise_batch Executable
---
RenderMan 25/26's [denoise_batch](https://rmanwiki-26.pixar.com/space/REN26/19661811/Denoiser+Command+Line) executable unfortunately does not provide an argument to set the number of threads to use when denoising images, and as such, it uses all threads on the computer it runs on. This makes it very hard to manage `denoise_batch` jobs on a render farm without setting aside specific machines/blades specifically for denoising. However, there is a workaround.

Setting the `OMP_NUM_THREADS` environment variable [allows us to tell OpenMP](https://www.openmp.org/spec-html/5.0/openmpse50.html) (the multiprocessing library used by `denoise_batch`) how many threads to use.

## Examples
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
