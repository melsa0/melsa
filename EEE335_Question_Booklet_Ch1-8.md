# EEE335 – Computer Organization and Architecture
## Practice Question Booklet — Chapters 1–8
### Format: Multiple Choice (4-option), Fill-in-the-Blank, Long Answer

---

# PART A — MULTIPLE CHOICE QUESTIONS

*Choose the single best answer for each question.*

---

## CHAPTER 1 — Basic Concepts and Computer Evolution

**1.** Which of the following best distinguishes **computer organization** from **computer architecture**?

A) Architecture refers to the physical hardware, while organization refers to the software layers  
B) Architecture refers to attributes visible to the programmer, while organization refers to hardware details transparent to the programmer  
C) Organization defines the instruction set, while architecture defines the bus structures  
D) Architecture changes with every new model, while organization remains fixed across a product family  

**2.** The IAS computer, designed at Princeton's Institute for Advanced Studies, is significant primarily because it:

A) Was the first computer to use transistors instead of vacuum tubes  
B) Was the first computer to implement a superscalar pipeline  
C) Served as the prototype for all subsequent general-purpose computers by implementing the stored program concept  
D) Was the first commercially available personal computer  

**3.** In the IAS computer, the register that temporarily holds the right-hand instruction from a word in memory is called the:

A) Memory Buffer Register (MBR)  
B) Instruction Register (IR)  
C) Instruction Buffer Register (IBR)  
D) Program Counter (PC)  

**4.** Moore's Law originally stated that the number of transistors on a chip doubled approximately every:

A) 6 months  
B) 1 year  
C) 2 years  
D) 5 years  

**5.** Which Intel processor was the **first 32-bit** Intel machine and the first to support multitasking?

A) 8086  
B) 80286  
C) 80386  
D) 80486  

**6.** A **deeply embedded system** is best described as:

A) A system that requires a general-purpose operating system and supports multiple user applications  
B) A single-purpose device that uses a microcontroller, is not reprogrammable after fabrication, and has no user interaction  
C) A cluster of networked servers deployed for cloud computing  
D) A multicore processor chip with more than 64 cores  

**7.** The ARM processor architecture is primarily derived from which design principle?

A) Complex Instruction Set Computing (CISC)  
B) Very Long Instruction Word (VLIW)  
C) Reduced Instruction Set Computing (RISC)  
D) Explicitly Parallel Instruction Computing (EPIC)  

**8.** Which of the following is NOT a consequence of Moore's Law as described by Stallings?

A) Falling cost of computer logic and memory  
B) Increased electrical path length resulting in slower operating speed  
C) Reduction in power and cooling requirements  
D) Computers becoming smaller and more convenient  

---

## CHAPTER 2 — Performance Concepts

**9.** The ability to issue more than one instruction in every processor clock cycle is called:

A) Pipelining  
B) Branch prediction  
C) Superscalar execution  
D) Speculative execution  

**10.** In Amdahl's Law, if 90% of a program can be parallelized (f = 0.9) and an infinite number of processors are used, the maximum theoretical speedup is:

A) Infinite  
B) 100  
C) 10  
D) 90  

**11.** The **Harmonic Mean** is the preferred measure when:

A) Comparing execution times of programs on the same machine  
B) Computing normalized ratios relative to a reference machine  
C) Comparing **rate-based** measurements such as MFLOPS  
D) Calculating the total running time of a set of benchmarks  

**12.** The **Geometric Mean** has the important property that it:

A) Is always larger than the arithmetic mean  
B) Gives equal weight to all values in the dataset  
C) Gives consistent results regardless of which reference system is used for normalization  
D) Is directly proportional to the total execution time  

**13.** Little's Law states that the average number of items in a queuing system equals:

A) The average arrival rate divided by the average service rate  
B) The average arrival rate multiplied by the average time an item spends in the system  
C) The average service time multiplied by the number of servers  
D) The average departure rate multiplied by the system capacity  

**14.** The **RC delay** problem in processors arises because:

A) As transistors shrink, the resistance of wires increases and their capacitance increases, slowing electron flow  
B) Larger caches require more read cycles, increasing total resistance  
C) The clock rate is limited by the response time of the ALU  
D) Branch prediction hardware introduces extra RC stages in the pipeline  

**15.** In SPEC CPU2017 evaluation, the **rate metric** measures:

A) Time for a single task to complete  
B) Number of tasks a system can accomplish per unit time (throughput)  
C) The ratio of peak to base performance  
D) The energy consumed per unit of computation  

**16.** A **GPU** (Graphics Processing Unit) is most accurately described as:

A) A specialized I/O module for interfacing display adapters  
B) A core designed to perform parallel operations, originally on graphics data, and now used as a vector processor for general computation  
C) A type of multicore processor where all cores share a single clock domain  
D) A dedicated memory controller for frame-buffer management  

---

## CHAPTER 3 — Computer Function and Interconnection

**17.** Von Neumann architecture is based on which three key concepts?

A) Data stored separately from instructions; sequential execution; external bus arbitration  
B) Data and instructions in a single read-write memory; addressable by location; sequential execution  
C) Hardwired programs; dedicated address spaces for data and instructions; parallel execution  
D) Stored programs; distributed memory; non-sequential instruction fetching  

**18.** At the beginning of each instruction cycle, the processor fetches the next instruction using the address stored in which register?

A) IR (Instruction Register)  
B) MAR (Memory Address Register)  
C) PC (Program Counter)  
D) MBR (Memory Buffer Register)  

**19.** An interrupt that is generated by a **timer within the processor** to allow the operating system to perform functions on a regular basis is classified as:

A) Program interrupt  
B) Timer interrupt  
C) I/O interrupt  
D) Hardware failure interrupt  

**20.** In a **Direct Memory Access (DMA)** transfer, which of the following is true?

A) The CPU executes a special read instruction for each data word transferred  
B) The I/O module and main memory exchange data directly without the CPU reading or writing each word  
C) Data passes through the CPU's accumulator before being written to memory  
D) All data transfers are initiated and completed within a single instruction cycle  

**21.** The **address bus** in a computer system is primarily used to:

A) Carry data values between modules  
B) Synchronize timing among CPU, memory, and I/O  
C) Designate the source or destination of data on the data bus  
D) Carry interrupt request signals from I/O modules to the CPU  

**22.** Intel's Quick Path Interconnect (QPI) replaced the traditional shared bus primarily because:

A) Shared buses were incompatible with DDR4 memory  
B) At high data rates, shared bus synchronization and arbitration became impractical; QPI offers lower latency and higher data rates via direct pairwise connections  
C) QPI provided backward compatibility with legacy PCI devices  
D) Shared buses could not support more than two processors  

**23.** In PCIe, the **Transaction Layer (TL)** supports which four address spaces?

A) Register, Stack, Heap, Code  
B) Memory, Configuration, I/O, Message  
C) Data, Control, Status, Interrupt  
D) Physical, Link, Routing, Protocol  

**24.** Which type of interrupt occurs due to a **memory parity error or power failure**?

A) Program interrupt  
B) Timer interrupt  
C) I/O interrupt  
D) Hardware failure interrupt  

---

## CHAPTER 4 — Memory Hierarchy: Locality and Performance

**25.** **Spatial locality** is best described as the tendency of a program to:

A) Access the same memory location repeatedly within a short time period  
B) Access memory locations whose addresses are near one another  
C) Avoid accessing memory during I/O-intensive operations  
D) Cache frequently used data in processor registers  

**26.** Which access method is used by cache memory, where a word is retrieved based on a **portion of its contents** rather than its address?

A) Sequential access  
B) Direct access  
C) Random access  
D) Associative access  

**27.** In a two-level memory system, the average access time formula (where *h* is the hit ratio, *T1* is upper-level time, and *T2* is lower-level time) is:

A) T_avg = h + (1−h)·T2  
B) T_avg = h·T1 + (1−h)·T2  
C) T_avg = T1·T2 / h  
D) T_avg = T1 / h + T2 / (1−h)  

**28.** The memory hierarchy design principle that states **copies of the same data unit at adjacent levels must be consistent** is called:

A) Locality  
B) Inclusion  
C) Coherence  
D) Replacement  

**29.** Compared to faster memory, larger-capacity memory tends to have which characteristic?

A) Higher cost per bit and faster access time  
B) Lower cost per bit and slower access time  
C) Lower cost per bit and faster access time  
D) Higher cost per bit and slower access time  

**30.** **Memory cycle time** differs from access time in that it:

A) Excludes the time needed to write data back after a destructive read  
B) Includes additional time required before a second access can begin (e.g., signal transients to die out)  
C) Applies only to non-volatile memories  
D) Measures only the data transfer rate, not the initial latency  

---

## CHAPTER 5 — Cache Memory

**31.** In **direct-mapped cache** with *m* cache lines, block *j* of main memory maps to cache line number:

A) j × m  
B) j + m  
C) j mod m  
D) m mod j  

**32.** In a **fully associative** cache, a memory block can be placed:

A) Only in one specific line determined by the block number  
B) In any line within a specific set  
C) In any line within the entire cache  
D) Only in the line whose tag matches the most significant bits of the address  

**33.** A **2-way set-associative** cache is one in which:

A) Each set contains 2 lines, and a given block can reside in either of those 2 lines  
B) Each block can map to exactly 2 possible lines anywhere in the cache  
C) The cache has 2 sets, and each set contains all lines  
D) The cache holds 2 copies of each block for redundancy  

**34.** Which replacement algorithm replaces the block that has been in the cache the **longest** regardless of recent usage?

A) LRU (Least Recently Used)  
B) FIFO (First In First Out)  
C) LFU (Least Frequently Used)  
D) Random  

**35.** In a **write-back** cache policy, when a word in the cache is modified:

A) The write is immediately propagated to main memory AND the cache  
B) Only the cache is updated; main memory is updated only when the block is replaced  
C) The block is immediately invalidated in the cache  
D) The write is buffered in the I/O module and flushed periodically  

**36.** **Write-through** cache policy is most associated with which write-miss alternative?

A) Write allocate  
B) No write allocate  
C) Victim buffer  
D) Prefetch on write  

**37.** A cache is considered **inclusive** when:

A) A piece of data in L1 is guaranteed NOT to be in L2 or L3  
B) A piece of data in L1 is guaranteed to also be present in all lower levels (L2, L3)  
C) Data is placed only in the cache that last referenced it  
D) Cache lines are split between instruction and data  

**38.** The main advantage of a **split cache** (separate I-cache and D-cache) over a **unified cache** is:

A) Higher overall hit rate because both caches benefit from a combined working set  
B) Elimination of cache contention between the instruction fetch unit and the execution unit  
C) Lower hardware cost because two smaller caches are cheaper than one large cache  
D) Simpler implementation because replacement algorithms can be different  

**39.** **Content-Addressable Memory (CAM)** is used in associative caches because it:

A) Stores data and its address together to allow faster writes  
B) Searches all lines in parallel in a single clock cycle based on a bit pattern  
C) Compresses data to allow more entries in the same physical space  
D) Provides error correction by storing redundant bit patterns  

**40.** As block size increases beyond an optimal point in a cache, the hit ratio begins to **decrease** because:

A) Larger blocks require more tags, consuming cache capacity  
B) The probability of using the newly fetched data becomes less than the probability of reusing replaced data  
C) The MMU takes longer to translate virtual addresses for larger blocks  
D) Larger blocks increase the miss penalty by requiring more bus cycles  

---

## CHAPTER 6 — Internal Memory

**41.** DRAM stores binary values as:

A) States of flip-flop circuits  
B) Magnetic polarization on a thin film  
C) Charge on capacitors  
D) Phase states of a crystalline material  

**42.** Compared to DRAM, SRAM is:

A) Slower, cheaper, and requires periodic refresh  
B) Faster, more expensive, and does not require refresh  
C) Slower, more expensive, and does not require refresh  
D) Faster, cheaper, and requires periodic refresh  

**43.** Which type of ROM can be **erased using ultraviolet light** and can be rewritten multiple times?

A) PROM  
B) EPROM  
C) EEPROM  
D) Flash memory  

**44.** Flash memory differs from EEPROM primarily in that:

A) Flash memory uses UV light for erasure instead of electrical signals  
B) Flash memory erases data at the **block level** rather than byte-by-byte  
C) Flash memory is volatile while EEPROM is nonvolatile  
D) Flash memory uses two transistors per bit while EEPROM uses one  

**45.** The Hamming SEC-DED code is capable of:

A) Correcting up to two bit errors and detecting up to four bit errors  
B) Correcting single-bit errors and detecting double-bit errors  
C) Detecting single-bit errors only, with no correction capability  
D) Correcting two-bit errors with no detection of larger errors  

**46.** **Interleaved memory** improves performance by:

A) Using faster SRAM chips in parallel with slower DRAM  
B) Storing consecutive words in different banks so that K banks can service K requests simultaneously  
C) Doubling the data bus width to transfer two words per cycle  
D) Caching frequently accessed rows in a buffer within the DRAM chip  

**47.** SDRAM (Synchronous DRAM) improves over conventional DRAM primarily by:

A) Using flip-flops instead of capacitors for more reliable storage  
B) Exchanging data synchronously with the external clock, allowing the processor to issue a command and then do other work while the DRAM processes  
C) Eliminating the need for periodic refresh by using a crystal oscillator  
D) Storing data in two phases simultaneously to double the effective bandwidth  

**48.** DDR SDRAM achieves higher data rates compared to regular SDRAM primarily by:

A) Using NOR flash cells instead of capacitors for faster read access  
B) Transferring data on **both the rising and falling edges** of the clock signal  
C) Doubling the number of memory banks and interleaving all accesses  
D) Using a dedicated point-to-point link for each memory module  

**49.** In the context of nonvolatile RAM, **STT-RAM** stores binary data using:

A) The phase state (amorphous vs. crystalline) of a chalcogenide material  
B) The direction of magnetization in a free magnetic layer  
C) The formation and dissolution of a conductive filament in a metal oxide  
D) Charge trapped in a floating gate transistor  

**50.** What is the primary advantage of **eDRAM** over off-chip DRAM?

A) eDRAM is nonvolatile and retains data when power is removed  
B) eDRAM is integrated on the same chip as the processor, providing faster access through wider buses  
C) eDRAM uses flash cells which are faster and cheaper than DRAM capacitors  
D) eDRAM does not require refresh cycles, reducing control overhead  

---

## CHAPTER 7 — External Memory

**51.** The total **block access time** for a magnetic disk is:

A) Seek time only  
B) Seek time + Rotational latency  
C) Seek time + Rotational latency + Transfer time  
D) Rotational latency + Transfer time only  

**52.** **Winchester heads** are distinguished from conventional disk heads by:

A) Being physically in contact with the disk surface at all times  
B) Being designed to operate inside sealed drive assemblies very close to the disk surface, lifted by aerodynamic force during operation  
C) Using magnetoresistive sensors instead of inductive coils for reading  
D) Being fixed (non-movable) to eliminate seek time  

**53.** Which RAID level provides **data striping with NO redundancy**?

A) RAID 1  
B) RAID 3  
C) RAID 5  
D) RAID 0  

**54.** RAID 5 distributes parity information across all disks rather than storing it on a dedicated parity disk. The main benefit of this approach compared to RAID 4 is:

A) Reduced write time because parity no longer needs to be computed  
B) Elimination of the parity-disk I/O bottleneck during write operations  
C) Ability to survive two simultaneous disk failures instead of one  
D) Higher sequential read transfer rate for large files  

**55.** RAID 6 requires how many extra disks beyond the number of data disks?

A) 0 (no extra disks)  
B) 1 extra disk  
C) 2 extra disks  
D) log₂(N) extra disks  

**56.** One practical issue specific to SSDs that HDDs do not face is:

A) High seek time due to mechanical arm movement  
B) Rotational latency because the disk must spin to the correct sector  
C) Flash cells wearing out after a finite number of write cycles, requiring wear-leveling  
D) High power consumption due to spindle motor  

**57.** Blu-ray discs achieve greater storage density than DVDs primarily by using:

A) A shorter-wavelength **blue-violet laser (405 nm)** allowing smaller pits and tracks  
B) A higher-capacity polycarbonate substrate that allows deeper pits  
C) Four recording layers instead of two on a double-sided DVD  
D) Magnetic rather than optical recording on the polycarbonate surface  

**58.** In RAID 3, data is distributed in **small strips across N+1 disks** where the extra disk:

A) Stores a mirrored copy of the entire dataset  
B) Contains Hamming error correction codes  
C) Stores a **simple parity bit** computed from corresponding bit positions on all data disks  
D) Stores an index of all block locations for fast random access  

**59.** Which RAID level is described as "block-interleaved distributed parity" and is most commonly used for file servers, database servers, and web servers?

A) RAID 1  
B) RAID 3  
C) RAID 4  
D) RAID 5  

**60.** A **CD-RW** disc differs from a CD-R disc primarily in that:

A) CD-RW uses a magnetic coating while CD-R uses a dye layer  
B) CD-RW uses a **phase-change material** that can be switched between amorphous and crystalline states, allowing multiple rewrites  
C) CD-RW holds 4× more data because it uses two recording layers  
D) CD-RW can only be written once but at a higher speed than CD-R  

---

## CHAPTER 8 — Input/Output

**61.** In **programmed I/O**, the CPU:

A) Passes control to a DMA controller immediately after issuing the I/O command  
B) Issues an I/O command and then **busy-waits** (polls the I/O module status) until the operation is complete  
C) Issues an I/O command, executes other instructions, and is interrupted when the I/O completes  
D) Relies on the I/O module to independently write data to memory without CPU involvement  

**62.** The primary drawback of both programmed I/O and interrupt-driven I/O compared to DMA is:

A) Both require the OS to manage memory mapping for I/O devices  
B) Each data word transfer requires CPU involvement, limiting transfer rate and tying up the processor  
C) Both methods require special I/O instructions not available in all ISAs  
D) Both methods require dedicated hardware buses that conflict with the main memory bus  

**63.** In **DMA**, the CPU provides the DMA controller with which initial information?

A) The exact instruction sequence to transfer each byte  
B) The starting address of the data block, the block length, and the transfer direction  
C) Only the device address; the DMA controller calculates all other parameters  
D) The interrupt vector and priority level for the transfer  

**64.** In **memory-mapped I/O**, I/O devices and memory:

A) Share a common address space; I/O operations use the same read/write instructions as memory  
B) Use separate address spaces; a special I/O select line distinguishes I/O from memory accesses  
C) Communicate only through a dedicated interrupt controller  
D) Each have their own dedicated bus with no shared signals  

**65.** A **daisy chain** interrupt identification scheme uses:

A) Software polling of each device register in a fixed priority order  
B) Multiple independent interrupt lines, one per device  
C) An interrupt acknowledge signal chained through all devices; the first device in the chain with a pending interrupt captures it and places its vector on the bus  
D) A bus arbitration protocol where all devices compete to send their interrupt vector  

**66.** **Direct Cache Access (DCA / DDIO)** was developed to address the limitation that:

A) DMA cannot handle transfers smaller than one cache line  
B) DMA-based network I/O at 10 Gbps and above causes excessive cache pollution by writing packets to main memory and then re-fetching them into cache  
C) The interrupt-driven I/O latency was too high for real-time systems  
D) Flash memory SSDs require a specialized DMA protocol incompatible with standard DMA  

**67.** An I/O module issues a **Test command** to:

A) Activate a peripheral device and instruct it to prepare for a transfer  
B) Take an item of data from the data bus and transmit it to the peripheral  
C) Obtain data from the peripheral and place it in an internal buffer  
D) Check various **status conditions** associated with the I/O module and its peripherals  

**68.** USB 3.1 (SuperSpeed+) achieves a signaling rate of:

A) 480 Mbps  
B) 5 Gbps  
C) 10 Gbps  
D) 40 Gbps  

**69.** FireWire (IEEE 1394) supports which of the following features that SCSI does not?

A) Parallel transmission to achieve higher data rates  
B) **Hot plugging** — connecting/disconnecting peripherals without powering down the system — and automatic configuration  
C) A dedicated memory controller for each connected device  
D) Simultaneous transfer to up to 256 devices on a single bus  

**70.** A **multiplexor I/O channel** differs from a **selector channel** in that:

A) A multiplexor channel handles one high-speed device at a time exclusively  
B) A selector channel can handle multiple slow-speed devices simultaneously  
C) A multiplexor channel can handle **multiple devices simultaneously**, while a selector channel serves one device at a time  
D) A multiplexor channel operates only in burst mode, while a selector channel operates in byte mode  

---

# PART B — FILL-IN-THE-BLANK QUESTIONS

*Write the single word or short phrase that best completes each statement.*

---

**B1.** The __________________ stores the address of the next instruction pair to be fetched from memory in the IAS computer.

**B2.** Gordon Moore observed in 1965 that the number of transistors on a chip was doubling approximately every __________________.

**B3.** The technique in which a processor analyzes data dependencies between instructions to create an optimized execution schedule is called __________________.

**B4.** According to Amdahl's Law, the theoretical speedup of a program is limited by its __________________ portion — the fraction that cannot be parallelized.

**B5.** The __________________ Mean is the preferred statistical measure when comparing rate-based performance metrics such as MFLOPS across different systems.

**B6.** The __________________ Mean gives consistent results regardless of which system is chosen as the normalization reference in benchmark comparisons.

**B7.** In the fetch-execute cycle, after each instruction fetch, the __________________ is incremented so that the processor will fetch the next sequential instruction.

**B8.** An interrupt generated by conditions such as arithmetic overflow, division by zero, or an illegal instruction is called a __________________ interrupt.

**B9.** In the QPI protocol, the unit of transfer at the link layer is called a __________________, which consists of a 72-bit payload and an 8-bit CRC.

**B10.** The principle that programs tend to reference memory locations near those they have recently accessed is called __________________ locality.

**B11.** A memory that is retrieved based on a **portion of its contents** rather than its address, and that retrieves in constant time, exhibits __________________ access.

**B12.** The memory design principle that dictates all data items are originally stored in the most remote level and copies flow upward is called __________________.

**B13.** In direct-mapped cache, if there are *m* cache lines, block *j* of main memory is mapped to cache line number __________________.

**B14.** The cache replacement algorithm that replaces the block that has been in the cache the **longest without being referenced** is called __________________ (write the full name).

**B15.** A write policy in which all write operations are made to both the cache and main memory simultaneously is called __________________.

**B16.** A write-miss handling strategy in which the block is **not** loaded into the cache after a write miss is called __________________.

**B17.** DRAM stores binary values as charge on __________________, while SRAM stores binary values using __________________ logic configurations.

**B18.** The type of ROM that is erased by **ultraviolet light** (chip-level erasure) is called __________________.

**B19.** The error correction code that can correct single-bit errors and detect double-bit errors is the __________________ code.

**B20.** SDRAM improves over conventional DRAM by exchanging data __________________ to an external clock signal, allowing the processor to do other work while the SDRAM processes.

**B21.** DDR SDRAM achieves double the data rate of SDRAM by transferring data on both the __________________ and __________________ edges of the clock signal.

**B22.** The total block access time for a magnetic disk is the sum of __________________, __________________, and __________________.

**B23.** RAID __________________ provides mirroring (complete duplication of data) and requires twice the number of data disks.

**B24.** RAID 5 stores parity information in a __________________ fashion across all disks in the array, eliminating the I/O bottleneck of a dedicated parity disk.

**B25.** In SSDs, the technique that evenly distributes write operations across all blocks to extend the device's lifetime is called __________________.

**B26.** Blu-ray discs use a __________________ nm wavelength laser, compared to 650 nm for DVD and 780 nm for CD.

**B27.** In the three I/O techniques, the method that transfers an entire block of data directly between I/O and memory **without involving the CPU for each word** is called __________________.

**B28.** In programmed I/O, the CPU repeatedly checks the status of the I/O module in a loop. This behavior is called __________________ (two words).

**B29.** When I/O devices and memory **share a single address space**, and normal memory read/write instructions are used for I/O, the scheme is called __________________ I/O.

**B30.** An I/O channel that can handle **multiple slow-speed I/O devices simultaneously** is called a __________________ channel.

---

# PART C — LONG ANSWER QUESTIONS

*Provide detailed answers. Include definitions, comparisons, diagrams (in text), or example calculations where appropriate.*

---

**LA1.** *(Chapter 1 & 2)*  
Compare and contrast **computer architecture** and **computer organization**, giving one concrete example of each. Then explain Moore's Law, state the rate at which transistor density has doubled since the 1970s, and describe **three significant consequences** of Moore's Law for computer systems.

---

**LA2.** *(Chapter 2)*  
**(a)** Explain **Amdahl's Law** in your own words. Write the speedup formula and explain each variable.  
**(b)** A program takes 100 seconds to execute on a single processor. 80% of the program is parallelizable. Calculate the speedup when using 4 processors and when using 16 processors. Show all work.  
**(c)** What does Amdahl's Law imply about the practical limits of parallel processing? Why is this significant for multicore processor design?

---

**LA3.** *(Chapter 2)*  
Three computers are evaluated on two programs:

| | Computer A | Computer B | Computer C |
|---|---|---|---|
| Program 1 (10⁸ FP ops) | 2.0 sec | 1.0 sec | 0.5 sec |
| Program 2 (10⁸ FP ops) | 0.5 sec | 2.0 sec | 1.0 sec |

**(a)** Calculate the **Arithmetic Mean** of execution times for each computer.  
**(b)** Calculate the **Harmonic Mean** of the MFLOPS rates for each computer. (MFLOPS = 10⁸ FP ops / time in seconds)  
**(c)** Normalize the results to Computer A and compute the **Geometric Mean** of the normalized times for each computer.  
**(d)** Which computer performs best overall, and which mean is most appropriate for comparing these results? Justify your answer.

---

**LA4.** *(Chapter 3)*  
Describe the **three I/O techniques** available in a computer system: programmed I/O, interrupt-driven I/O, and DMA.  
**(a)** For each technique, explain: (i) how the transfer is initiated, (ii) what the CPU does while the transfer takes place, and (iii) how the CPU is informed that the transfer is complete.  
**(b)** Draw a simple timeline or describe the sequence of events for each.  
**(c)** When would you choose DMA over interrupt-driven I/O? What are the two inherent drawbacks shared by programmed I/O and interrupt-driven I/O?

---

**LA5.** *(Chapter 4)*  
Explain the **principle of locality** including its two forms. Then describe the **memory hierarchy** of a modern computer system, listing at least 4 levels from fastest to slowest. For each level, state the typical technology used, the typical access time range, and who manages that level (compiler, hardware, or OS).

---

**LA6.** *(Chapter 5)*  
A computer has a main memory of **16 MB** (16,777,216 bytes) and a cache of **16K lines**. Each cache line holds **4 bytes** (one word). The memory address is **24 bits**.  
**(a)** For **direct-mapped cache**: Calculate the number of bits for the Tag, Line, and Word fields. Show the address partition.  
**(b)** For **fully associative cache**: Calculate the number of bits for the Tag and Word fields.  
**(c)** For **2-way set-associative cache**: Calculate the number of sets, and the bits for Tag, Set, and Word fields.  
**(d)** Compare the three mapping methods: What is the main advantage and disadvantage of each?

---

**LA7.** *(Chapter 5)*  
**(a)** Explain the difference between **write-through** and **write-back** cache write policies. Describe the advantage of each.  
**(b)** Explain **write-allocate** and **no-write-allocate** write-miss policies. Which is most commonly paired with each write policy and why?  
**(c)** Explain the **cache coherency problem** in a multiprocessor system. Describe two approaches used to address cache coherency.

---

**LA8.** *(Chapter 6)*  
**(a)** Compare **SRAM** and **DRAM** in terms of: storage mechanism, need for refresh, speed, cost, density, and typical use in a computer system (cache vs. main memory).  
**(b)** List and briefly describe the five types of ROM/read-mostly memory: ROM, PROM, EPROM, EEPROM, and Flash Memory. For each, state how it is written and how it is erased.  
**(c)** Explain how the **Hamming SEC-DED code** provides error correction. How many check bits are needed for 8 data bits (SEC only) and for 16 data bits (SEC-DED)? Use the table from the textbook.

---

**LA9.** *(Chapter 7)*  
**(a)** Define and explain the three components of disk access time: seek time, rotational latency, and transfer time. Which is typically the largest contributor to total access time and why?  
**(b)** Describe **RAID levels 0, 1, 3, and 5** including: the number of disks required (relative to N data disks), the redundancy mechanism used, whether the access is parallel or independent, and the primary use case for each.  
**(c)** What are the two practical problems unique to SSDs compared to HDDs? How are they addressed?

---

**LA10.** *(Chapter 8)*  
**(a)** Describe the **evolution of the I/O function** through all six stages identified by Stallings. For each stage, explain what change was made and how it improved efficiency.  
**(b)** Explain the difference between **memory-mapped I/O** and **isolated (separate) I/O**. Give one advantage of each approach.  
**(c)** Explain how **DCA (Direct Cache Access / DDIO)** works and why it was developed. What problem does it solve that regular DMA cannot?

---

# ANSWER KEY — MULTIPLE CHOICE

| Q | A | Q | A | Q | A | Q | A |
|---|---|---|---|---|---|---|---|
| 1 | B | 11 | C | 21 | C | 31 | C |
| 2 | C | 12 | C | 22 | B | 32 | C |
| 3 | C | 13 | B | 23 | B | 33 | A |
| 4 | B | 14 | A | 24 | D | 34 | B |
| 5 | C | 15 | B | 25 | B | 35 | B |
| 6 | B | 16 | B | 26 | D | 36 | B |
| 7 | C | 17 | B | 27 | B | 37 | B |
| 8 | B | 18 | C | 28 | C | 38 | B |
| 9 | C | 19 | B | 29 | B | 39 | B |
| 10 | C | 20 | B | 30 | B | 40 | B |

| Q | A | Q | A | Q | A | Q | A |
|---|---|---|---|---|---|---|---|
| 41 | C | 51 | C | 61 | B | — | — |
| 42 | B | 52 | B | 62 | B | — | — |
| 43 | B | 53 | D | 63 | B | — | — |
| 44 | B | 54 | B | 64 | A | — | — |
| 45 | B | 55 | C | 65 | C | — | — |
| 46 | B | 56 | C | 66 | B | — | — |
| 47 | B | 57 | A | 67 | D | — | — |
| 48 | B | 58 | C | 68 | C | — | — |
| 49 | B | 59 | D | 69 | B | — | — |
| 50 | B | 60 | B | 70 | C | — | — |

---

# ANSWER KEY — FILL-IN-THE-BLANK

| # | Answer |
|---|---|
| B1 | Program Counter (PC) |
| B2 | One year (updated to 18 months from the 1970s onward) |
| B3 | Data flow analysis |
| B4 | Sequential |
| B5 | Harmonic |
| B6 | Geometric |
| B7 | Program Counter (PC) |
| B8 | Program |
| B9 | Flit (flow control unit) |
| B10 | Spatial |
| B11 | Associative |
| B12 | Inclusion |
| B13 | j mod m |
| B14 | Least Recently Used (LRU) |
| B15 | Write-through |
| B16 | No write allocate |
| B17 | Capacitors; flip-flop |
| B18 | EPROM |
| B19 | Hamming |
| B20 | Synchronously |
| B21 | Rising; falling |
| B22 | Seek time; rotational latency (delay); transfer time |
| B23 | RAID 1 |
| B24 | Distributed |
| B25 | Wear leveling |
| B26 | 405 |
| B27 | DMA (Direct Memory Access) |
| B28 | Busy waiting (polling) |
| B29 | Memory-mapped |
| B30 | Multiplexor |

---

*End of Question Booklet*
*Good luck on your final exam!*
