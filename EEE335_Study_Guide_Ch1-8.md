# EEE335 – Computer Organization and Architecture
## Comprehensive Study Guide — Chapters 1–8
### Stallings, *Computer Organization and Architecture*, 11th Edition

---

## CHAPTER 1 — Basic Concepts and Computer Evolution

### Computer Architecture vs. Organization
| Term | Meaning |
|---|---|
| **Architecture** | Attributes visible to the programmer (instruction set, data types, I/O mechanisms, memory addressing techniques) |
| **Organization** | Operational units and their interconnections (hardware details transparent to the programmer: control signals, memory technology) |

*Same architecture, different organization → IBM System/370 family (customer software protected across generations)*

### Structure and Function
- **Structure**: how components relate to each other
- **Function**: operation of individual components as part of the structure
- Four basic computer **functions**: Data Processing, Data Storage, Data Movement, Control

### Four Main Structural Components
1. **CPU** – controls operation, performs data processing
2. **Main Memory** – stores data
3. **I/O** – moves data between computer and external environment
4. **System Interconnection** – provides communication among above three

### CPU Components
- Control Unit, ALU, Registers, CPU Interconnection

### IAS Computer (von Neumann Architecture)
- Designed at Princeton Institute for Advanced Studies (completed 1952)
- **Stored program concept**: instructions and data stored in a single read-write memory
- Prototype of all subsequent general-purpose computers
- 40-bit words: number word (sign + 39-bit magnitude) or instruction word (two 20-bit instructions)

**IAS Registers:**
| Register | Function |
|---|---|
| MBR (Memory Buffer Register) | Contains word to be stored/received from memory |
| MAR (Memory Address Register) | Address of word to be read/written |
| IR (Instruction Register) | 8-bit opcode of current instruction |
| IBR (Instruction Buffer Register) | Temporarily holds right-hand instruction |
| PC (Program Counter) | Address of next instruction pair |
| AC (Accumulator) | Operands and results of ALU |
| MQ (Multiplier-Quotient) | Operands and results of ALU |

### Integrated Circuits and Moore's Law
- **Transistors** are the fundamental building block
- **Moore's Law** (1965, Gordon Moore): transistor count on a chip doubles roughly every 18 months
- Consequences: falling cost, shorter electrical paths, higher speed, smaller size, lower power

### Intel Processor Evolution Highlights
- **8080**: first general-purpose microprocessor (8-bit), used in Altair
- **8086**: 16-bit, first x86 architecture; instruction cache (prefetch queue)
- **80386**: Intel's first 32-bit machine, first to support multitasking
- **80486**: sophisticated cache + instruction pipelining; built-in math coprocessor
- **Pentium**: superscalar techniques (multiple instructions in parallel)
- **Pentium Pro**: register renaming, branch prediction, speculative execution
- **Core 2**: 64-bit, 2 or 4 cores; Advanced Vector Extensions (AVX)

### Multicore Terminology
- **CPU**: portion that fetches and executes instructions
- **Core**: individual processing unit on a chip
- **Processor**: physical silicon piece containing one or more cores

### Embedded Systems
- Electronics + software within a product
- Often have **real-time constraints**
- **Deeply embedded system**: microcontroller, not programmable after fabrication, no user interaction, wireless-capable sensor/actuator
- **ARM**: RISC-based, most widely used embedded processor architecture; Cortex-A, Cortex-R, Cortex-M families
- **IoT (Internet of Things)**: fourth generation of deployment; billions of single-purpose devices

---

## CHAPTER 2 — Performance Concepts

### Techniques to Increase Processor Speed
| Technique | Description |
|---|---|
| **Pipelining** | Multiple instructions processed simultaneously at different stages |
| **Branch Prediction** | Processor predicts future instruction branches |
| **Superscalar Execution** | Issue more than one instruction per clock cycle (multiple parallel pipelines) |
| **Data Flow Analysis** | Schedule instructions based on data dependencies |
| **Speculative Execution** | Execute likely future instructions ahead of time |

### Performance Balance
Mismatch between processor speed and memory/I/O speed is the **performance balance problem**. Solutions:
- Wider DRAM buses
- More complex cache structures
- DRAM on-chip buffering
- Higher-speed buses and bus hierarchy

### Problems with Increasing Clock Speed
- **Power**: higher density → more heat
- **RC delay**: resistance and capacitance of wires increase; thinner wires = higher resistance; closer wires = higher capacitance
- **Memory latency and throughput**: memory access speeds lag behind processor speeds

### Multicore
- Use two or more simpler processors on one chip instead of one complex processor
- Justifies larger caches; leads to L2 and L3 caches
- Does NOT increase clock rate

### GPU and MIC
- **GPU**: core designed for parallel operations on graphics data; used as vector processor
- **MIC (Many Integrated Core)**: large number of general-purpose cores on one chip

### Amdahl's Law
$$\text{Speedup} = \frac{1}{(1-f) + \frac{f}{N}}$$
- *f* = fraction of the program that can be parallelized
- *N* = number of processors
- Even with infinite processors, speedup is limited by the sequential portion (1−f)

### Little's Law
$$N = \lambda \cdot W$$
- *N* = average number of items in system
- *λ* = average arrival rate
- *W* = average time an item spends in the system

### Means for Performance Comparison
| Mean | Best Used For | Property |
|---|---|---|
| **Arithmetic Mean (AM)** | Execution times | Proportional to total time; gives equal weight to all values |
| **Harmonic Mean (HM)** | Rates (e.g., MFLOPS) | Preferred when comparing rates |
| **Geometric Mean (GM)** | Normalized (ratio) results | Consistent regardless of reference system used |

### SPEC Benchmarks (CPU2017)
- Industry consortium (System Performance Evaluation Corporation)
- **Benchmark suite**: collection of high-level programs representing a given application area
- **Base metric**: required, strict compilation guidelines
- **Peak metric**: allows compiler optimization
- **Speed metric**: time to complete a single task (task completion ability)
- **Rate metric**: tasks per unit time (throughput)
- SPEC CPU2017: 20 integer + 23 floating-point benchmarks; results use geometric mean of ratios

---

## CHAPTER 3 — A Top-Level View of Computer Function and Interconnection

### Von Neumann Concepts
1. Data and instructions stored in a single read-write memory
2. Memory contents addressable by location (not data type)
3. Execution is sequential unless explicitly modified

### CPU Registers (Top-Level View)
| Register | Function |
|---|---|
| PC | Address of next instruction |
| IR | Instruction being executed |
| MAR | Memory address for next R/W |
| MBR | Data to write / received from memory |
| I/OAR | Address of specific I/O device |
| I/OBR | Data exchange buffer between I/O module and CPU |

### Instruction Cycle
1. **Fetch cycle**: PC → MAR; memory → MBR; MBR → IR; PC incremented
2. **Execute cycle**: decode IR; perform action
- Four action categories: Processor-Memory, Processor-I/O, Control (branching), Data Processing

### Interrupts
| Type | Cause |
|---|---|
| Program | Arithmetic overflow, divide-by-zero, illegal instruction, memory violation |
| Timer | Generated by internal timer for OS functions |
| I/O | Completion of I/O operation, request for service, error |
| Hardware Failure | Power failure, parity error |

**With interrupts**: CPU issues I/O command → continues executing → interrupted when I/O done → executes interrupt handler → resumes
**Multiple interrupts**: sequential (disable interrupts while handling) or nested (allow higher-priority interrupts)

### Direct Memory Access (DMA)
- I/O module granted authority to read/write main memory directly
- No CPU involvement for each data item during transfer
- CPU involved only at beginning and end of transfer

### Bus Structure
- **Bus**: shared communication pathway
- **Data Bus**: carries data (32, 64, 128+ lines); width = key performance factor
- **Address Bus**: designates source/destination; width determines max memory capacity
- **Control Bus**: carries command/timing signals (read, write, interrupt, clock)
- **System Bus**: connects processor, memory, and I/O

### Point-to-Point Interconnect
- Replaced shared bus due to electrical constraints at high frequencies
- Lower latency, higher data rate, better scalability

### QPI (Quick Path Interconnect) — Intel
- Direct pairwise connections (no arbitration)
- Layered protocol: Physical → Link → Routing → Protocol
- Packetized data transfer with CRC error control
- Flit (flow control unit) = 72-bit payload + 8-bit CRC

### PCI Express (PCIe)
- Point-to-point, high-bandwidth
- Layered protocol: Physical → Data Link → Transaction
- Transaction Layer (TL): address spaces — Memory, Configuration, I/O, Message
- Uses split transactions: request packet + completion packet

---

## CHAPTER 4 — The Memory Hierarchy: Locality and Performance

### Principle of Locality
- Programs tend to cluster memory references
- **Temporal locality**: recently referenced items likely to be referenced again soon (loops, variables)
- **Spatial locality**: items near recently accessed items likely to be referenced (sequential access, arrays)

### Memory Characteristics
| Characteristic | Options |
|---|---|
| Location | Internal (registers, cache, main memory) / External (disk, tape) |
| Capacity | Number of bytes |
| Unit of Transfer | Word (random access) / Block |
| Access Method | Sequential / Direct / Random / Associative |
| Physical Type | Semiconductor / Magnetic / Optical |
| Volatility | Volatile / Nonvolatile |

**Access Methods:**
- **Sequential**: linear, variable access time (tape)
- **Direct**: unique address by physical location, variable access time (disk)
- **Random**: any location directly, constant access time (RAM)
- **Associative**: retrieved based on content, constant time (cache)

### Performance Parameters
- **Access time (latency)**: time for a read/write
- **Memory cycle time**: access time + additional time before next access (bus-oriented)
- **Transfer rate**: 1 / cycle time for random access

### Memory Hierarchy: Trade-off
- **Faster** → more expensive, smaller capacity
- **Larger** → cheaper per bit, slower access
- Hierarchy exploits locality to achieve near-fast-memory performance at near-large-memory cost

### Memory Hierarchy Levels (typical)
| Level | Technology | Managed by |
|---|---|---|
| Registers | CMOS | Compiler |
| Cache | SRAM / eDRAM | Processor hardware |
| Main Memory | DRAM | OS |
| Secondary | Magnetic disk | OS / User |
| Offline | Magnetic tape | OS / User |

### Two-Level Memory Performance
- Hit ratio *h* = fraction of accesses found in upper (faster) level
- Average access time: T_avg = h·T1 + (1−h)·T2
- For performance ≈ T1, need high h (high locality)

### Design Principles for Memory Hierarchy
- **Locality**: makes hierarchy effective
- **Inclusion**: all data originally at deepest level; copies flow up
- **Coherence**: copies at adjacent levels must be consistent

---

## CHAPTER 5 — Cache Memory

### Key Terminology
- **Block**: minimum unit of transfer between cache and main memory
- **Frame** (block frame): chunk of physical cache that holds one block
- **Line**: portion of cache holding one block (horizontal in diagrams)
- **Tag**: portion of cache line used for addressing
- **Line size**: number of data bytes in a line

### Cache Read Operation
1. Receive address RA from CPU
2. Check if block containing RA is in cache
   - **Hit**: fetch word → deliver to CPU
   - **Miss**: access main memory → allocate cache line → load block → deliver word to CPU

### Elements of Cache Design

#### 1. Cache Addresses
- **Logical (virtual) cache**: before MMU translation; faster but aliasing problems
- **Physical cache**: after MMU translation; more common in modern systems

#### 2. Cache Size
- Larger = higher hit rate, but larger caches are slightly slower and more expensive
- No single optimum; depends on workload

#### 3. Mapping Functions

**Direct Mapping**
- Each block maps to exactly one cache line: `line = block mod m` (where m = number of cache lines)
- Address split: Tag | Line | Word
- Simple, fast; **conflict misses** possible (only one block can occupy a given line)

**Fully Associative Mapping**
- Any block can be placed in any cache line
- Address split: Tag | Word
- Uses Content-Addressable Memory (CAM); searches all lines in parallel
- Flexible, no conflict misses; expensive hardware

**Set-Associative Mapping**
- Cache divided into *v* sets, each with *k* lines (m = v × k)
- Block maps to one set; within that set, any line → *k*-way set associative
- Address split: Tag | Set | Word
- Compromise: moderate hardware cost, fewer conflict misses than direct

#### 4. Replacement Algorithms (for Associative and Set-Associative)
| Algorithm | Description |
|---|---|
| **LRU** (Least Recently Used) | Replace block with no reference for longest time; most effective; most popular |
| **FIFO** (First In First Out) | Replace oldest block; round-robin implementation |
| **LFU** (Least Frequently Used) | Replace block with fewest references; needs counters |
| **Random** | Simple implementation; surprisingly close to LRU in practice |

*(Direct mapping: no choice; only one possible line per block)*

#### 5. Write Policy
| Policy | Description | Advantage | Disadvantage |
|---|---|---|---|
| **Write-Through** | All writes go to main memory AND cache | Main memory always up-to-date | High memory traffic, potential bottleneck |
| **Write-Back** | Write only to cache; update main memory when block is replaced | Reduces memory writes | Complex; I/O access must go through cache; potential bottleneck |

**Write Miss Alternatives:**
- **Write Allocate**: load block into cache before writing (usually with write-back)
- **No Write Allocate**: write directly to main memory, not loaded into cache (usually with write-through)

#### 6. Cache Coherency (Multiprocessor Systems)
- Multiple processors sharing memory → invalidation problem
- Approaches: bus watching with write-through, hardware transparency, noncacheable memory

#### 7. Line Size
- Larger blocks → better spatial locality → higher hit ratio (initially)
- Too large → probability of using newly fetched data decreases → lower hit ratio
- Typical: 32–128 bytes

#### 8. Number of Caches
- **Multilevel caches**: L1 (on-chip, fastest), L2, L3
- **Unified cache**: single cache for instructions and data (higher hit rate, simpler)
- **Split cache**: separate I-cache and D-cache (eliminates contention; important for pipelining)
- Modern trend: split L1, unified L2/L3

#### 9. Inclusion Policy
- **Inclusive**: data in L1 always also in L2/L3 (simplifies coherence checking)
- **Exclusive**: data in one level not duplicated in others (maximizes capacity)
- **Noninclusive**: data may or may not be in lower levels

---

## CHAPTER 6 — Internal Memory

### Semiconductor Memory Types
| Type | Category | Erasure | Volatility |
|---|---|---|---|
| RAM | Read-write | Electrically, byte-level | Volatile |
| ROM | Read-only | Not possible | Nonvolatile |
| PROM | Read-only | Not possible (write once) | Nonvolatile |
| EPROM | Read-mostly | UV light, chip-level | Nonvolatile |
| EEPROM | Read-mostly | Electrically, byte-level | Nonvolatile |
| Flash | Read-mostly | Electrically, block-level | Nonvolatile |

### DRAM (Dynamic RAM)
- Stores data as charge on **capacitors**
- Presence/absence of charge = binary 1 or 0
- Requires **periodic refresh** (charge leaks away)
- Simpler, smaller, denser, cheaper
- Used for **main memory**

### SRAM (Static RAM)
- Uses **flip-flop** logic gate configurations
- Holds data as long as power is on (no refresh needed)
- Faster, more expensive, less dense
- Used for **cache memory**

### ROM Types
- **ROM**: permanent, no-write; data wired in during fabrication
- **PROM**: write electrically once; flexible, convenient for high-volume runs
- **EPROM**: erasable with UV light (chip-level); rewritable multiple times
- **EEPROM**: electrically erasable byte-by-byte; most flexible nonvolatile memory before flash
- **Flash Memory**: electrically erased block-by-block; intermediate cost/functionality between EPROM and EEPROM; uses one transistor per bit (high density)

### Error Correction
- **Hard failure**: permanent physical defect; cell stuck at 0 or 1
- **Soft error**: random, non-destructive; caused by power supply issues or alpha particles
- **Hamming Code**: can correct single-bit errors and detect double-bit errors (SEC-DED)
- More data bits → fewer extra check bits needed (proportionally)
- 8 data bits needs 4 check bits (SEC) or 5 check bits (SEC-DED)

### Interleaved Memory
- Memory divided into K banks
- K banks can service K requests simultaneously
- Consecutive words stored in different banks → block transfers sped up by factor K

### Advanced DRAM
| Type | Key Feature |
|---|---|
| **SDRAM** | Synchronized to external clock; no wait states; processor can do other work while SDRAM processes |
| **DDR SDRAM** | Transfers on both rising and falling clock edges; higher bus clock rate; prefetch buffer |
| **DDR2** | 4-bit prefetch buffer; 1.8V; 400–1066 Mbps |
| **DDR3** | 8-bit prefetch buffer; 1.5V; 800–2133 Mbps |
| **DDR4** | 8-bit prefetch buffer; 1.2V; 2133–4266 Mbps |
| **eDRAM** | DRAM integrated on same chip as processor; faster than off-chip DRAM |

### Flash Memory Details
- **NOR flash**: random access, good for code execution; lower density
- **NAND flash**: block access, good for file storage; higher density, lower cost per bit
- Limited write endurance → wear-leveling algorithms, bad-block management

### Nonvolatile RAM Technologies
- **STT-RAM** (Spin-Transfer Torque): magnetic orientation; fast, byte-addressable
- **PCRAM** (Phase Change): amorphous vs crystalline state; good endurance
- **ReRAM** (Resistive): filament formation changes resistance; simple structure

---

## CHAPTER 7 — External Memory

### Magnetic Disk (HDD)
- Circular platter (substrate + magnetizable coating)
- Substrate: traditionally aluminum; increasingly glass (better uniformity, lower defects)
- **Read/write head** moves over spinning platter
- **Track**: concentric circle on a surface
- **Sector**: subdivision of a track (smallest addressable unit)
- **Cylinder**: all tracks at the same radial position across all surfaces

### Disk Performance Parameters
| Parameter | Definition |
|---|---|
| **Seek time** | Time to move head to the correct track |
| **Rotational latency (delay)** | Time for beginning of desired sector to reach the head |
| **Transfer time** | Time to read/write the data once head is in position |
| **Access time (Block access time)** | Seek time + Rotational latency + Transfer time |

### Physical Characteristics of Disks
- **Fixed-head**: one head per track; no seek time; expensive
- **Movable-head**: one head per surface; most common
- **Non-removable**: permanently mounted (HDD)
- **Removable**: can be exchanged (floppy, ZIP)
- **Winchester heads**: aerodynamic foil; sealed drive; operates very close to disk surface for greater data density

### RAID (Redundant Array of Independent Disks)
All RAID levels share: (1) single logical drive view, (2) data striping, (3) parity for redundancy

| Level | Name | Disks | Description | Key Feature |
|---|---|---|---|---|
| **RAID 0** | Nonredundant | N | Striping only | Highest I/O rate; no redundancy; one failure loses all data |
| **RAID 1** | Mirrored | 2N | Complete duplication | 100% overhead; fast reads; simple recovery |
| **RAID 2** | Hamming code | N+m | Bit-level striping with Hamming ECC | No commercial implementation; very high transfer rates |
| **RAID 3** | Bit-interleaved parity | N+1 | Bit-level striping, single parity disk | Highest transfer rate; poor transaction rate |
| **RAID 4** | Block-interleaved parity | N+1 | Block-level striping, dedicated parity | Write penalty (4 operations per write); not commercially viable |
| **RAID 5** | Distributed parity | N+1 | Block-level striping, parity distributed across all disks | Most versatile; no parity disk bottleneck; used in file servers, DB servers |
| **RAID 6** | Dual distributed parity | N+2 | Two independent parities | Can survive two simultaneous disk failures; highest availability |

### Solid State Drives (SSD)
- Based on NAND flash memory
- **Advantages over HDD**: high IOPS, durable, longer lifespan, lower power, quieter, lower latency
- **Disadvantage**: higher cost per GB, limited write endurance
- **Practical issue 1**: performance degrades as blocks become partially written (must read-erase-write)
- **Practical issue 2**: flash cells wear out after a number of writes → **wear leveling**

### Optical Memory
| Type | Description |
|---|---|
| CD-ROM | Read-only; 650+ MB; pits on polycarbonate |
| CD-R | Write once, read many; permanent record |
| CD-RW | Rewritable; phase change material (amorphous/crystalline) |
| DVD-ROM | Up to 17 GB (double-sided, dual layer); read-only |
| DVD-R / DVD-RW | Recordable/rewritable versions |
| Blu-ray | 405 nm (blue-violet) laser; 25 GB per layer; HD video |

- CD: 780 nm laser; 2.11 µm beam; 1.2 µm track pitch
- DVD: 650 nm laser; 1.32 µm beam; 0.6 µm track pitch
- Blu-ray: 405 nm laser; 0.58 µm beam; 0.1 µm track pitch

### Magnetic Tape
- Sequential recording; data in contiguous blocks separated by inter-record gaps
- Used for backup and archival storage

---

## CHAPTER 8 — Input/Output

### External Devices
- **Human readable**: VDTs, printers (IRA/ASCII codes)
- **Machine readable**: magnetic disk/tape, sensors, actuators
- **Communication**: modem, network interface

### I/O Module Functions
1. **Control and Timing**: coordinate traffic flow
2. **Processor Communication**: command decoding, data transfer, status reporting
3. **Device Communication**: command, status, data with peripheral
4. **Data Buffering**: balance speed mismatch between device and memory
5. **Error Detection**: detect and report transmission errors

### Three I/O Techniques
| Technique | CPU Role | Memory Involved | Interrupts |
|---|---|---|---|
| **Programmed I/O** | Issues command, **busy-waits** (polls status) | Via CPU | No |
| **Interrupt-driven I/O** | Issues command, continues other work, handles interrupt | Via CPU | Yes |
| **DMA (Direct Memory Access)** | Issues block command; continues; interrupted only at end | Direct (no CPU) | Yes (at end) |

### I/O Commands
1. **Control**: activate peripheral, tell it what to do
2. **Test**: check status conditions
3. **Read**: obtain data from peripheral → buffer
4. **Write**: take data from data bus → send to peripheral

### I/O Mapping
| Type | Address Space | Commands | Notes |
|---|---|---|---|
| **Memory-Mapped I/O** | Shared with memory | Regular memory read/write | Large instruction set available |
| **Isolated (Separate) I/O** | Separate from memory | Special I/O instructions | I/O or memory select lines needed; limited instruction set |

### Interrupt-Driven I/O: Device Identification
- **Multiple interrupt lines**: direct; impractical for many devices
- **Software poll**: interrupt service routine polls each device; time-consuming
- **Daisy chain (hardware poll, vectored)**: interrupt acknowledge chained; device puts vector on bus
- **Bus arbitration (vectored)**: device must win bus arbitration before raising interrupt

### DMA (Direct Memory Access)
- DMA controller takes over system bus for block transfers
- CPU provides: starting address, block length, transfer direction
- CPU interrupted only when block transfer is complete
- **Fly-by DMA**: data goes directly from I/O to memory (not through DMA chip)
- 8237 DMA chip: 4 channels, independently programmable

### DMA Configurations
- Single-bus, detached DMA
- Single-bus, integrated DMA-I/O
- I/O bus (separate bus for I/O devices)

### Direct Cache Access (DCA)
- DMA cannot scale for 10 Gbps / 100 Gbps Ethernet
- **DCA / Cache injection**: NIC writes incoming packet data directly into CPU cache, bypassing main memory
- Implemented as Intel's **Direct Data I/O (DDIO)** on Xeon processors

### Evolution of I/O Function
1. CPU directly controls peripheral
2. Controller added; programmed I/O, no interrupts
3. Same as 2, but with interrupts (efficiency ↑)
4. DMA added: block transfers without CPU
5. I/O module becomes processor with specialized I/O instruction set
6. I/O module has local memory → full I/O computer; minimal CPU involvement

### I/O Channels
- **Selector channel**: controls one high-speed device at a time (e.g., disk)
- **Multiplexor channel**: handles multiple slow devices simultaneously

### External Interconnection Standards
| Standard | Key Facts |
|---|---|
| **USB** | Default for slow/medium peripherals; tree topology via root hub; USB 3.1 = 10 Gbps |
| **FireWire (IEEE 1394)** | Up to 63 devices daisy-chained; hot-plugging; automatic configuration; developed as SCSI alternative |
| **SCSI** | Parallel bus; 16–32 devices; 5–160 Mbps; high-speed versions for enterprise storage |
| **Thunderbolt** | Intel + Apple; 10 Gbps each direction + 10W power; combines data, video, audio |
| **InfiniBand** | High-end server market; switch-based; up to 64,000 devices; storage area networking |
| **SATA** | Serial interface for disk storage; up to 6 Gbps |
| **PCIe** | High-speed peripheral bus; up to 300 Mbps per device |
| **Ethernet** | Wired networking; up to 100 Gbps; switched architecture |
| **Wi-Fi (802.11ac)** | Wireless; up to 3.2 Gbps |

---

## KEY FORMULAS SUMMARY

| Formula | Meaning |
|---|---|
| `line = block mod m` | Direct-mapped cache: line number |
| `T_avg = h·T1 + (1-h)·(T1+T2)` ≈ `h·T1 + (1-h)·T2` | Two-level memory average access time |
| `Speedup = 1 / [(1-f) + f/N]` | Amdahl's Law |
| `N = λ · W` | Little's Law |
| `AM = Σxi / n` | Arithmetic Mean |
| `HM = n / Σ(1/xi)` | Harmonic Mean |
| `GM = (Π xi)^(1/n)` | Geometric Mean |
| Access time = Seek + Rotational Latency + Transfer | Disk access time |

---

*Study tip: Focus on Chapters 5–8 for the final, but Chapters 1–4 may appear. Review all mapping/replacement examples in Chapter 5, RAID level characteristics in Chapter 7, and the three I/O techniques in Chapter 8.*
