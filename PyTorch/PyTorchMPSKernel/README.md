---
layout: post
title: Giving PyTorch Control Over A Metal MPS Kernel
---
There isn't a lot of up-to-date documentation online on how to efficiently call custom Metal Performance Shader (MPS) Kernels through PyTorch in Objective C++.

A useful tutorial is this one by [smrfeld on GitHub](https://github.com/smrfeld/pytorch-cpp-metal-tutorial). I'd recommend going through that first to help get your bearings on first setting up an MPS Kernel for PyTorch, however, the section on calling Metal kernels from C++ is out of date. I have updated the example Obj-C++ extension code from the tutorial above and included it in the GitHub repo for this site, [which you can find here](https://github.com/jonahjnewton/TDVault/blob/main/PyTorch/PyTorchMPSKernel/cpp_extension.mm).

Below, I will go into more detail about what has changed with PyTorch's MPS backend since that article was written.

## Providing Tensor Pointers to Argument Buffers
When setting up a compute pipeline in Metal, we need to set up argument buffers to pass our tensors to the MPS Kernel. The trick, however, comes down to ensuring ownership of the argument buffer memory remains with PyTorch rather than inefficiently needing to copy memory over to a region that Metal controls, and then back to PyTorch. For example, if we pass a tensor to our kernel to use, we need to make sure our kernel has access to that memory location.

Luckily, we can access the tensor's storage and pass it directly to our kernel.
#### Before
```objc++
// Create output Tensor object
torch::Tensor output_tensor = torch::zeros_like(input_img);

// Create Metal buffer which points to the output tensor
id<MTLBuffer> outputTensorBuffer = [device newBufferWithBytes:output_tensor.data_ptr() length:(numElements * sizeof(float)) options:MTLResourceStorageModeShared];

// Setup command queue, buffer, and encoder
...

// Point argument index 0 in our kernel to our output tensor buffer
[encoder setBuffer:outputTensorBuffer offset:0 atIndex:0];
```
#### Now
```objc++
// Helper function to retrieve the `MTLBuffer` from a `torch::Tensor`.
static inline id<MTLBuffer> getMTLBufferStorage(const torch::Tensor& tensor) {
  return __builtin_bit_cast(id<MTLBuffer>, tensor.storage().data());
}

// Compute pipeline setup
...

// Create output Tensor object
torch::Tensor a = torch::zeros_like(input_img);

// Point argument index 0 in our kernel to the Metal buffer created by PyTorch for our output tensor
[encoder setBuffer:getMTLBufferStorage(a) offset:a.storage_offset() a.element_size() atIndex:0];
```

Providing the tensor's MTLBuffer storage setup by PyTorch means that not only do we no longer need to manage the tensor's memory allocation, but it gives PyTorch full control over the setup and management of the tensor's memory. Any changes made to this tensor in our kernel directly update the tensor in C++, which is then passed back to Python.

## Command Buffer and Queue
PyTorch also gives us a command queue and buffer to utilise via `torch::mps::get_dispatch_queue()` and `torch::mps::get_command_buffer()` respectively, rather than needing to create them ourselves. This gives PyTorch complete control over the buffer used to store commands to send to the GPU, and the queue with which these commands are sent to the GPU. When we are done setting up the call to the kernel, we use `torch::mps::commit()` to let PyTorch manage adding the command to the buffer/the queue.
#### Before
```objc++
// Create command queue
id<MTLCommandQueue> commandQueue = [device newCommandQueue];

// Create command buffer in our command queue
id<MTLCommandBuffer> commandBuffer = [commandQueue commandBuffer];

// Setup encoder, and dispatch kernel
...

// Commit command to the command queue
[commandBuffer commit];

// Don't continue this thread until the command buffer is done
[commandBuffer waitUntilCompleted];
```

#### Now
```objc++
// Get PyTorch's Metal command buffer
id<MTLCommandBuffer> cb = torch::mps::get_command_buffer();

// Get PyTorch's Metal command queue
dispatch_queue_t serialQueue = torch::mps::get_dispatch_queue();

// Ensures command buffers sent to the queue are processed synchronously (see Notes section)
dispatch_sync(serialQueue, ^{
	// Setup encoder, and dispatch kernel
	...
	
	// Tell PyTorch to commit the call to the kernel 
	torch::mps::commit();
}
```

## Further Reading

* The only other article I can find with this updated info is [this one by Praburam](https://medium.com/@praburam_93885/custom-pytorch-operations-for-metal-backend-889736c6bc2a), which is based on [this sample code from Apple](https://developer.apple.com/documentation/metal/customizing-a-pytorch-operation?language=objc). 

## Notes
* In the new queue code, we add a `dispatch_sync` call to ensure any blocks submitted to the queue are run synchronously. This code is visible in all code I can find using this new method, including [Apple's example code](https://developer.apple.com/documentation/metal/customizing-a-pytorch-operation?language=objc). I am unsure if this is necessary in *all* PyTorch MPS kernel calls due to Torch's MPS backend's command queue being explicitly synchronous (Apple's example code specifies the variable `serialQueue`, so this may be the case), or if it might be possible to also utilise async kernel calls with PyTorch. From my testing I didn't see any difference between using `dispatch_async` and `dispatch_sync`, but further investigation is needed.
* [Apple's example code](https://developer.apple.com/documentation/metal/customizing-a-pytorch-operation?language=objc) wraps the Metal device initialisation and handling in an `@autorelease` statement, which is used in Metal to ensure temporary objects are released at the end of the statement, rather than waiting until the end of the block to release. This is not directly related to PyTorch, but is still worth reading into to understand how to reduce peak memory usage in your functions.
