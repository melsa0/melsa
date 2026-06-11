# EEE335 – Bilgisayar Organizasyonu ve Mimarisi
## Türkçe Özet — Chapter 1–8
### Stallings, *Computer Organization and Architecture*, 11. Baskı

---

## CHAPTER 1 — Temel Kavramlar ve Bilgisayar Evrimi

### Computer Architecture vs. Computer Organization
- **Computer Architecture**: Programcıya görünen özellikler — instruction set, veri türleri, I/O mekanizmaları, bellek adresleme. Programın mantıksal çalışmasını doğrudan etkiler.
- **Computer Organization**: Programcıdan gizli donanım detayları — control signals, ara yüzler, bellek teknolojisi. Architecture'ı gerçekleştiren fiziksel birimlerin bağlantıları.
- **Örnek**: IBM System/370 ailesi; aynı architecture, farklı organization → eski yazılım korunur.

### Structure (Yapı) ve Function (İşlev)
- **Structure**: Bileşenlerin birbiriyle ilişkisi
- **Function**: Her bileşenin yapı içindeki işlevi
- Bir bilgisayarın dört temel işlevi: **Data Processing**, **Data Storage**, **Data Movement**, **Control**

### Dört Ana Yapısal Bileşen
1. **CPU** — kontrolü sağlar, veri işler
2. **Main Memory** — veri depolar
3. **I/O** — dış dünya ile veri alışverişi
4. **System Interconnection** — yukarıdakileri birbirine bağlar (system bus)

### IAS Bilgisayarı (von Neumann Architecture)
- Princeton Institute for Advanced Studies'te tasarlandı; 1952'de tamamlandı.
- **Stored program concept**: veri ve instructions aynı read-write memory'de tutulur.
- Tüm modern general-purpose bilgisayarların prototipidir.
- Her word 40 bittir: sayı kelimesi (sign + 39-bit magnitude) veya instruction word (iki adet 20-bit instruction).

**IAS Register'ları:**
| Register | Türkçe Açıklama |
|---|---|
| **MBR** (Memory Buffer Register) | Bellekten gelen veya belleğe gidecek word'ü tutar |
| **MAR** (Memory Address Register) | Okunacak/yazılacak adres |
| **IR** (Instruction Register) | Çalıştırılan 8-bit opcode |
| **IBR** (Instruction Buffer Register) | Sağ instruction'ı geçici tutar |
| **PC** (Program Counter) | Sonraki instruction çiftinin adresi |
| **AC** (Accumulator) | ALU işlemleri için geçici depolama |
| **MQ** (Multiplier-Quotient) | Çarpma/bölme için ALU yardımcısı |

### Integrated Circuits ve Moore's Law
- **Transistor**: dijital devrelerin temel yapı taşı.
- **Moore's Law** (1965, Gordon Moore): chip üzerindeki transistor sayısı her yıl ikileniyordu; 1970'lerden itibaren tempo 18 ayda bir ikiye düştü.
- Sonuçları: düşen maliyet, kısalan elektrik yolu → daha yüksek hız, küçülen boyut, azalan güç tüketimi.

### Intel İşlemci Evrimi (Önemli Olanlar)
| İşlemci | Önem |
|---|---|
| **8080** | İlk general-purpose microprocessor (8-bit); Altair PC'de kullanıldı |
| **8086** | 16-bit; ilk x86 architecture; instruction cache (prefetch queue) |
| **80386** | Intel'in ilk 32-bit makinesi; multitasking desteği |
| **80486** | Gelişmiş cache + instruction pipelining; built-in math coprocessor |
| **Pentium** | Superscalar (paralel instruction çalıştırma) |
| **Pentium Pro** | Register renaming, branch prediction, speculative execution |
| **Core 2** | 64-bit; 2 veya 4 core; Advanced Vector Extensions (AVX) |

### Çok Çekirdekli (Multicore) Terminoloji
- **CPU**: instruction fetch ve execute eden kısım
- **Core**: chip üzerindeki bireysel işlem birimi
- **Processor**: bir veya daha fazla core içeren fiziksel silikon parça

### Embedded Systems ve IoT
- Bir ürünün içine gömülmüş elektronik + yazılım sistemi.
- **Real-time constraints**: çevreyle etkileşim gerektiren zamanlama kısıtları.
- **Deeply embedded system**: microcontroller tabanlı; fabrikasyon sonrası programlanamaz; kullanıcı arayüzü yok; kablosuz sensör/aktüatör.
- **ARM**: RISC tabanlı; dünyada en yaygın kullanılan embedded processor architecture; Cortex-A, Cortex-R, Cortex-M serileri.
- **IoT (Internet of Things)**: milyarlarca tek amaçlı cihazın birbirine bağlanması.

---

## CHAPTER 2 — Performance Concepts

### İşlemci Hızını Artırma Teknikleri
| Teknik | Ne Yapar? |
|---|---|
| **Pipelining** | Birden fazla instruction eş zamanlı farklı aşamalarda işlenir |
| **Branch Prediction** | Processor gelecekteki branch'leri önceden tahmin eder |
| **Superscalar Execution** | Her clock cycle'da birden fazla instruction işlenir (paralel pipeline) |
| **Data Flow Analysis** | Instruction'lar arasındaki veri bağımlılıkları analiz edilir, optimum sıra oluşturulur |
| **Speculative Execution** | Muhtemelen gerekecek instruction'lar önceden çalıştırılır |

### Performance Balance Problemi
- Processor hızı ile memory/I/O hızı arasındaki **uyumsuzluk**.
- Çözümler: daha geniş DRAM bus, karmaşık cache yapıları, DRAM'de on-chip buffer, yüksek hızlı bus hiyerarşisi.

### Clock Hızını Artırmanın Sorunları
- **Power (Güç)**: yoğunluk arttıkça daha fazla ısı üretilir.
- **RC delay**: tel incelince direnç artar; teller yaklaştıkça kapasitans artar → elektron akışı yavaşlar.
- **Memory latency**: bellek erişim hızı, işlemci hızının gerisinde kalır.

### Multicore, MIC, GPU
- **Multicore**: tek chip üzerinde birden fazla processor; clock hızını artırmadan performance iyileştirme.
- **MIC (Many Integrated Core)**: büyük sayıda general-purpose core.
- **GPU (Graphics Processing Unit)**: paralel işlemler için tasarlanmış core; grafik + genel amaçlı vektör hesaplama.

### Amdahl's Law
$$\text{Speedup} = \frac{1}{(1 - f) + \dfrac{f}{N}}$$
- *f*: paralel çalıştırılabilir kısım oranı
- *N*: işlemci sayısı
- **Ana mesaj**: ne kadar çok işlemci eklenirse eklensin, hız kazanımı sıralı (sequential) kısım tarafından sınırlandırılır. Sonsuz işlemciyle bile maksimum speedup = 1/(1−f).

### Little's Law
$$N = \lambda \cdot W$$
- *N*: sistemdeki ortalama öğe sayısı
- *λ*: ortalama varış hızı
- *W*: bir öğenin sistemde geçirdiği ortalama süre
- Neredeyse hiç varsayım gerektirmez; çok geniş uygulama alanı.

### Ortalama Hesaplama Yöntemleri
| Ortalama | Ne Zaman? | Özelliği |
|---|---|---|
| **Arithmetic Mean (AM)** | Çalışma sürelerini karşılaştırırken | Toplam süreyle doğru orantılı |
| **Harmonic Mean (HM)** | MFLOPS gibi rate bazlı ölçümlerde | Rate ölçümleri için tercih edilir |
| **Geometric Mean (GM)** | Normalize edilmiş (ratio) sonuçlarda | Hangi referans sistem seçilirse seçilsin tutarlı sonuç verir |

### SPEC Benchmarks (CPU2017)
- **SPEC**: System Performance Evaluation Corporation — industry consortium.
- **Benchmark suite**: belirli bir uygulama alanını temsil eden high-level program koleksiyonu.
- **Base metric**: tüm sonuçlar için zorunlu, katı derleme kuralları.
- **Peak metric**: derleyici optimizasyonuna izin verir.
- **Speed metric**: tek bir görevin tamamlanma süresi (task completion).
- **Rate metric**: birim zamanda tamamlanan görev sayısı (throughput).
- Sonuçlar geometric mean of ratios ile hesaplanır.

---

## CHAPTER 3 — Bilgisayarın Üst Düzey Yapısı ve Birbirbağlantıları

### Von Neumann Architecture — Üç Temel Kavram
1. Veri ve instruction'lar tek bir read-write memory'de saklanır.
2. Memory içeriği konum (adres) ile erişilebilir; veri türüne bakılmaz.
3. Çalışma sıralı (sequential) olarak ilerler; aksi explicitly belirtilmedikçe.

### Üst Düzey Register'lar
| Register | İşlev |
|---|---|
| **PC** | Sıradaki instruction'ın adresi |
| **IR** | Çalıştırılan instruction |
| **MAR** | Bellek okuma/yazma adresi |
| **MBR** | Bellekten gelen / belleğe gidecek veri |
| **I/OAR** | I/O cihaz adresi |
| **I/OBR** | I/O modülü ile CPU arasındaki veri tamponu |

### Instruction Cycle (Fetch–Execute)
1. **Fetch cycle**: PC → MAR; memory'den MBR'ye word okunur → IR'ye yüklenir; PC artırılır.
2. **Execute cycle**: IR decode edilir; işlem gerçekleştirilir.
- Dört eylem kategorisi: **Processor-Memory**, **Processor-I/O**, **Control** (branch), **Data Processing**

### Interrupt Türleri
| Tür | Sebep |
|---|---|
| **Program** | Arithmetic overflow, sıfıra bölme, illegal instruction, izinsiz bellek erişimi |
| **Timer** | İşlemci içindeki timer; OS fonksiyonlarını düzenli çalıştırmak için |
| **I/O** | I/O işleminin tamamlanması, servis isteği, hata |
| **Hardware Failure** | Güç kesintisi, bellek parity hatası |

**Interrupt ile I/O akışı**: CPU komut verir → başka işlem yapar → I/O tamamlanınca interrupt → interrupt handler çalışır → CPU kaldığı yerden devam eder.

**Birden fazla interrupt**: sıralı (sequential) işleme veya iç içe (nested) işleme (önceliğe göre).

### DMA (Direct Memory Access)
- I/O modülüne belleği doğrudan okuma/yazma yetkisi verilir.
- CPU her word transferi için müdahale etmez; sadece başında ve sonunda dahil olur.

### Bus Yapısı
- **Bus**: paylaşımlı iletişim yolu; tüm bağlı cihazlar sinyalleri duyar.
- **Data Bus**: veri taşır (32, 64, 128+ hat); genişlik = önemli performans faktörü.
- **Address Bus**: kaynak/hedef adresi belirtir; genişlik = max bellek kapasitesini belirler.
- **Control Bus**: komut ve zamanlama sinyalleri (read, write, interrupt, clock).
- **System Bus**: CPU, bellek ve I/O'yu birbirine bağlar.

### Point-to-Point Interconnect
- Yüksek frekanslarda paylaşımlı bus'ın senkronizasyon sorunu → **point-to-point** bağlantı.
- Daha düşük latency, daha yüksek data rate, daha iyi scalability.

### QPI (Quick Path Interconnect) — Intel
- Doğrudan ikili bağlantılar; arbitration gerekmez.
- Katmanlı protokol: Physical → Link → Routing → Protocol.
- **Flit** (flow control unit) = 72-bit payload + 8-bit CRC.
- Paketlenmiş veri transferi.

### PCI Express (PCIe)
- Point-to-point, yüksek bant genişliği, processor-independent.
- Katmanlı protokol: Physical → Data Link → Transaction.
- **Transaction Layer (TL)** adres uzayları: Memory, Configuration, I/O, Message.
- Split transaction: request packet → completion packet.

---

## CHAPTER 4 — Bellek Hiyerarşisi: Locality ve Performance

### Locality (Yerellik) İlkesi
- Programlar bellekten rastgele değil, **küme halinde** erişim yapar.
- **Temporal locality**: yakın geçmişte erişilen adrese yakın gelecekte tekrar erişilme eğilimi (döngüler, geçici değişkenler).
- **Spatial locality**: yakın zamanda erişilen adreslere yakın adreslere de erişilme eğilimi (diziler, sıralı kodlar).

### Bellek Karakteristikleri
| Özellik | Seçenekler |
|---|---|
| Konum | Internal (register, cache, main memory) / External (disk, tape) |
| Kapasite | Byte sayısı |
| Transfer birimi | Word (random access) / Block |
| Erişim yöntemi | Sequential / Direct / Random / Associative |
| Fiziksel tür | Semiconductor / Magnetic / Optical |
| Uçuculuk | Volatile / Nonvolatile |

**Erişim yöntemleri:**
- **Sequential**: lineer sıra, değişken erişim süresi (manyetik teyp).
- **Direct**: fiziksel konumla benzersiz adres, değişken erişim süresi (disk).
- **Random**: her konum doğrudan erişilebilir, sabit erişim süresi (RAM).
- **Associative**: içeriğin bir kısmıyla erişim, sabit süre (cache).

### Performans Parametreleri
- **Access time (latency)**: okuma/yazma süresi.
- **Memory cycle time**: erişim süresi + bir sonraki erişim için bekleme süresi (bus için geçerli).
- **Transfer rate**: 1 / cycle time (random access için).

### Bellek Hiyerarşisi — Temel Trade-off
- **Hızlı bellek** → pahalı, küçük kapasite.
- **Büyük kapasite** → bit başına ucuz, yavaş erişim.
- Hiyerarşi, locality sayesinde hem hızlı performans hem büyük kapasite görünümü sağlar.

### Tipik Hiyerarşi Seviyeleri
| Seviye | Teknoloji | Kim Yönetir? |
|---|---|---|
| Registers | CMOS | Derleyici |
| Cache | SRAM / eDRAM | Donanım (processor) |
| Main Memory | DRAM | OS |
| Secondary (Disk) | Magnetic disk | OS / Kullanıcı |
| Offline (Tape) | Magnetic tape | OS / Kullanıcı |

### İki Seviyeli Bellek Performansı
$$T_{avg} = h \cdot T_1 + (1-h) \cdot T_2$$
- *h*: hit ratio (üst seviyede bulunan erişim oranı)
- *T1*: üst seviye erişim süresi, *T2*: alt seviye erişim süresi
- Yüksek h → T_avg ≈ T1 (cache zamanı kadar hızlı).

### Hiyerarşi Tasarım İlkeleri
- **Locality**: hiyerarşiyi mümkün kılan temel ilke.
- **Inclusion**: veri en uzak seviyeden başlar; yukarı kopyalar oluşur.
- **Coherence**: komşu seviyelerdeki aynı verinin kopyaları tutarlı olmalıdır.

---

## CHAPTER 5 — Cache Memory

### Temel Terimler
- **Block**: cache ile main memory arasında transfer edilen minimum veri birimi.
- **Frame (block frame)**: cache'de bir block'u tutan fiziksel yer.
- **Line**: cache'de bir block'u tutan yatay birim; tag + data içerir.
- **Tag**: adreslemede kullanılan cache line'ın parçası.
- **Line size**: bir line'daki byte sayısı.

### Cache Okuma İşlemi
1. CPU'dan RA (adres) gelir.
2. Block cache'de var mı?
   - **Hit**: word doğrudan CPU'ya teslim edilir.
   - **Miss**: main memory'den block okunur → cache line ayrılır → block cache'e yüklenir → word CPU'ya verilir.

### Cache Tasarım Elemanları

#### 1. Cache Adresleri
- **Logical (virtual) cache**: MMU'dan önce; daha hızlı ama alias sorunları.
- **Physical cache**: MMU'dan sonra; modern sistemlerde yaygın.

#### 2. Mapping Function (Eşleme Fonksiyonu)

**Direct Mapping**
- Her main memory block'u tam olarak bir cache line'a eşlenir.
- Formül: `line = block mod m` (m = toplam cache line sayısı)
- Adres bölümü: **Tag | Line | Word**
- Avantaj: basit, hızlı. Dezavantaj: çakışma (conflict miss) riski yüksek.

**Fully Associative Mapping**
- Her block herhangi bir cache line'a yerleştirilebilir.
- Adres bölümü: **Tag | Word**
- Content-Addressable Memory (CAM) ile paralel arama — tek clock cycle.
- Avantaj: çakışma yok. Dezavantaj: pahalı hardware.

**Set-Associative Mapping**
- Cache *v* set'e bölünür; her set *k* line içerir (m = v × k). *k*-way set-associative.
- Block bir set'e eşlenir; o set içinde herhangi bir line'a gidebilir.
- Adres bölümü: **Tag | Set | Word**
- Orta yol: makul donanım maliyeti, az conflict miss.

#### 3. Replacement Algorithms (Değiştirme Algoritmaları)
| Algoritma | Açıklama |
|---|---|
| **LRU** (Least Recently Used) | En uzun süre erişilmemiş block'u çıkar; en etkili, en popüler |
| **FIFO** (First In First Out) | Cache'e en erken giren block'u çıkar; round-robin uygulaması |
| **LFU** (Least Frequently Used) | En az erişilen block'u çıkar; counter gerektirir |
| **Random** | Rastgele seçim; basit implementasyon |

*Not: Direct mapping'de seçim şansı yoktur; her block için tek bir olası line vardır.*

#### 4. Write Policy (Yazma Politikası)
| Politika | Nasıl Çalışır? | Avantaj | Dezavantaj |
|---|---|---|---|
| **Write-Through** | Yazma hem cache hem main memory'e yapılır | Main memory her zaman güncel | Yüksek memory trafiği, darboğaz riski |
| **Write-Back** | Yalnızca cache güncellenir; block çıkarılırken main memory güncellenir | Az memory trafiği | Karmaşık devre; I/O erişimi cache'den geçmeli |

**Write Miss Alternatifleri:**
- **Write Allocate**: block cache'e çekilir, sonra yazılır (genellikle write-back ile).
- **No Write Allocate**: doğrudan main memory'e yazılır, cache'e çekilmez (genellikle write-through ile).

#### 5. Cache Coherency (Çok İşlemcili Sistemler)
- Birden fazla processor kendi cache'ine sahipse, birinin cache'ini güncellemesi diğerlerini geçersiz kılar.
- Yaklaşımlar: write-through ile bus watching, hardware transparency, noncacheable memory.

#### 6. Line Size
- Büyük block → spatial locality'den daha fazla yararlanılır → hit ratio artar (başta).
- Çok büyük block → yeni getirilen verinin kullanılma ihtimali düşer → hit ratio düşer.
- Tipik: 32–128 byte.

#### 7. Multilevel Caches
- **L1** (on-chip, en hızlı), **L2**, **L3**.
- **Unified cache**: instruction + data birlikte; daha yüksek hit rate.
- **Split cache**: ayrı I-cache ve D-cache; pipelining için instruction fetch ile execution birimi çakışması önlenir.
- Modern eğilim: split L1, unified L2/L3.

#### 8. Inclusion Policy
- **Inclusive**: L1'deki veri L2 ve L3'te de kesinlikle vardır → cache coherence kolaylaşır.
- **Exclusive**: L1'deki veri alt seviyelerde yoktur → kapasite israfı olmaz.
- **Noninclusive**: L1'deki veri alt seviyelerde olabilir ya da olmayabilir.

---

## CHAPTER 6 — Internal Memory (İç Bellek)

### Yarı İletken Bellek Türleri
| Tür | Kategori | Silme Yöntemi | Uçuculuk |
|---|---|---|---|
| **RAM** | Read-write | Elektriksel (byte) | Volatile |
| **ROM** | Read-only | Mümkün değil | Nonvolatile |
| **PROM** | Read-only | Mümkün değil (bir kez yaz) | Nonvolatile |
| **EPROM** | Read-mostly | UV ışığı (chip düzeyinde) | Nonvolatile |
| **EEPROM** | Read-mostly | Elektriksel (byte düzeyinde) | Nonvolatile |
| **Flash** | Read-mostly | Elektriksel (block düzeyinde) | Nonvolatile |

### DRAM (Dynamic RAM)
- Veriyi **kapasitörler**deki yük olarak saklar.
- Yük sızar → **periyodik refresh** gerekli (bu yüzden "dynamic").
- Daha basit, daha küçük, daha yoğun, daha ucuz.
- **Main memory** için kullanılır.

### SRAM (Static RAM)
- Veriyi **flip-flop** devre yapılarıyla saklar.
- Güç varken refresh gerekmez.
- Daha hızlı, daha pahalı, daha az yoğun.
- **Cache memory** için kullanılır.

### ROM Türleri — Kısa Özet
- **ROM**: veri üretim sürecinde devreye işlenir; değiştirilemez.
- **PROM**: elektrikle bir kez programlanır (fuse yakma).
- **EPROM**: UV ışığıyla tüm chip silinir; defalarca yazılabilir.
- **EEPROM**: elektrikle byte bazında silinir; en esnek nonvolatile bellek (flash'tan önce).
- **Flash Memory**: elektrikle **block** bazında silinir; EPROM ile EEPROM arası maliyet/işlevsellik; bit başına yüksek yoğunluk (tek transistör). **NOR flash**: rastgele erişim, kod çalıştırma. **NAND flash**: yüksek yoğunluk, dosya saklama.

### Error Correction (Hata Düzeltme)
- **Hard failure**: kalıcı fiziksel arıza; cell sıkışık kalır.
- **Soft error**: geçici, yıkıcı olmayan; güç problemi veya alfa parçacıklarından.
- **Hamming Code (SEC-DED)**: tek bit hatalarını **düzeltir**, çift bit hatalarını **algılar**.
  - 8 data bit → 4 check bit (SEC) veya 5 check bit (SEC-DED)
  - 16 data bit → 5 check bit (SEC) veya 6 check bit (SEC-DED)

### Interleaved Memory
- K bank'a bölünmüş bellek; K bank eş zamanlı K isteğe hizmet edebilir.
- Ardışık word'ler farklı bank'larda saklanır → block transferi K kat hızlanır.

### Advanced DRAM Türleri
| Tür | Ana Özellik |
|---|---|
| **SDRAM** | Harici clock'a senkronize; CPU komut verir ve SDRAM işlerken başka şey yapabilir |
| **DDR SDRAM** | Clock'un hem yükselen hem düşen kenarında veri transfer eder → 2× data rate |
| **DDR2** | 4-bit prefetch; 1.8V; 400–1066 Mbps |
| **DDR3** | 8-bit prefetch; 1.5V; 800–2133 Mbps |
| **DDR4** | 8-bit prefetch; 1.2V; 2133–4266 Mbps |
| **eDRAM** | DRAM'in işlemci chip'iyle entegrasyonu; off-chip DRAM'den daha hızlı |

### Nonvolatile RAM Teknolojileri (Yeni Nesil)
- **STT-RAM**: manyetik katmanın yönelimi veri depolar; hızlı, byte erişimli.
- **PCRAM**: kristalin/amorf faz değişimi veri depolar; iyi dayanıklılık.
- **ReRAM**: metal oksitte iletken filament oluşumu/çözülmesi veri depolar; basit yapı.

---

## CHAPTER 7 — External Memory (Dış Bellek)

### Manyetik Disk (HDD)
- Dairesel plaka (substrate): geleneksel alüminyum, günümüzde cam (daha az defekt, daha yüksek yoğunluk).
- **Track**: yüzeydeki eş merkezli halka.
- **Sector**: track'in bölümü (en küçük adreslenebilir birim).
- **Cylinder**: tüm yüzeylerdeki aynı radyal konumdaki track'ler.
- **Head**: okuma/yazma kafası; plaka dönerken sabit durur.

### Disk Performans Parametreleri
| Parametre | Tanım |
|---|---|
| **Seek time** | Head'in doğru track'e taşınma süresi |
| **Rotational latency** | İstenen sector'ün head'in altına gelme süresi |
| **Transfer time** | Veri okunurken/yazılırken geçen süre |
| **Block access time** | Seek + Rotational latency + Transfer time |

### Fiziksel Disk Özellikleri
- **Fixed-head disk**: track başına bir head; seek yok; pahalı.
- **Movable-head disk**: yüzey başına bir head; en yaygın.
- **Winchester heads**: hava yastığıyla yüzen kafa; kapalı, sızdırmaz muhafaza; çok yüksek veri yoğunluğu.

### RAID (Redundant Array of Independent Disks)
Tüm RAID seviyeleri paylaşır: (1) tek logical disk görünümü, (2) data striping, (3) redundancy.

| Seviye | Adı | Gereken Disk | Açıklama | Kullanım Yeri |
|---|---|---|---|---|
| **RAID 0** | Nonredundant | N | Sadece striping; yedek yok | Video editing, yüksek bant genişliği |
| **RAID 1** | Mirrored | 2N | Tam kopyalama (mirroring) | Muhasebe, finansal uygulamalar |
| **RAID 2** | Hamming code | N+m | Bit düzeyinde striping + Hamming ECC | Ticari uygulama yok |
| **RAID 3** | Bit-interleaved parity | N+1 | Bit striping + tek parity disk | Video yayını, görüntü işleme |
| **RAID 4** | Block-interleaved parity | N+1 | Block striping + dedicated parity disk | Ticari uygulama yok |
| **RAID 5** | Distributed parity | N+1 | Block striping + parity tüm disklere dağıtılmış | Dosya/DB sunucuları, web sunucuları |
| **RAID 6** | Dual distributed parity | N+2 | İki bağımsız parity; iki eş zamanlı disk arızasına dayanır | Mission-critical uygulamalar |

### SSD (Solid State Drive)
- NAND flash belleğe dayalı.
- **HDD'ye göre avantajları**: yüksek IOPS, dayanıklı, uzun ömür, düşük güç, sessiz, düşük latency.
- **Dezavantajları**: bit başına yüksek maliyet, sınırlı yazma ömrü.
- **Pratik sorun 1**: blok kısmen doluysa write slowdown (sil → yaz döngüsü).
- **Pratik sorun 2**: flash cell'ler belirli sayıda yazmadan sonra bozulur → **wear leveling** algoritması.

### Optik Bellek
| Tür | Kapasite | Özellik |
|---|---|---|
| **CD-ROM** | ~650 MB | Salt okunur; polycarbonate üzeri çukur (pit) |
| **CD-R** | ~700 MB | Bir kez yazılır (WORM); boya katmanı |
| **CD-RW** | ~700 MB | Defalarca yeniden yazılır; phase-change malzeme |
| **DVD-ROM** | 4.7–17 GB | Salt okunur; çift katman/yüzey mümkün |
| **Blu-ray** | 25 GB/katman | 405 nm mavi-mor laser; HD video |

Laser dalga boyu: CD → 780 nm, DVD → 650 nm, Blu-ray → **405 nm** (kısa dalga boyu = daha küçük pit = daha fazla veri).

### Manyetik Teyp
- Sıralı (sequential) erişim; veri blokları inter-record gap'larla ayrılır.
- Yedekleme ve arşiv amaçlı kullanılır.

---

## CHAPTER 8 — Input/Output (Giriş/Çıkış)

### Dış Cihaz Kategorileri
- **Human readable**: ekran, yazıcı (IRA/ASCII kodları).
- **Machine readable**: manyetik disk/teyp, sensör, aktüatör.
- **Communication**: modem, network interface.

### I/O Module'ün Fonksiyonları
1. **Control and Timing**: trafik koordinasyonu
2. **Processor Communication**: komut decode, veri, durum raporu
3. **Device Communication**: periferale komut, durum, veri
4. **Data Buffering**: cihaz ile bellek hızı uyumsuzluğunu dengeler
5. **Error Detection**: hata tespiti ve raporlama

### Üç I/O Tekniği
| Teknik | CPU'nun Rolü | Memory Erişimi | Interrupt |
|---|---|---|---|
| **Programmed I/O** | Komut verir, **busy-wait** yapar (status sürekli sorgulanır) | CPU üzerinden | Hayır |
| **Interrupt-driven I/O** | Komut verir, başka iş yapar; I/O bitince **interrupt** alır | CPU üzerinden | Evet |
| **DMA** | Block komutu verir, başka iş yapar; sadece sonunda interrupt alır | Doğrudan (CPU yok) | Evet (sadece sonda) |

### I/O Komutları
1. **Control**: çevre birimini aktive et, ne yapacağını söyle.
2. **Test**: I/O modülünün çeşitli durum koşullarını kontrol et.
3. **Read**: çevre biriminden veri al → internal buffer.
4. **Write**: data bus'tan veri al → çevre birimine gönder.

### I/O Mapping (Adres Eşleme)
| Tür | Adres Uzayı | Kullanılan Komutlar | Not |
|---|---|---|---|
| **Memory-Mapped I/O** | Bellekle ortak | Normal memory read/write | Geniş instruction seti |
| **Isolated (Separate) I/O** | Bellekten ayrı | Özel I/O instruction | I/O select hattı gerekli; sınırlı komut seti |

### Interrupt-Driven I/O — Cihaz Tanımlama
- **Multiple interrupt lines**: her cihaz için ayrı hat; fazla cihazda impraktik.
- **Software poll**: interrupt service routine her cihazı sırayla sorgular; yavaş.
- **Daisy chain**: interrupt acknowledge sinyali cihazlardan zincirlenerek geçer; bekleyen cihaz kendi vektörünü bus'a koyar.
- **Bus arbitration**: cihaz önce bus'ı kazanmalı; sonra interrupt vektörünü verir.

### DMA — Nasıl Çalışır?
1. CPU, DMA denetleyicisine: başlangıç adresi, block uzunluğu, transfer yönü verir.
2. DMA, sistem bus'ını alarak veri transferini yapar; CPU başka iş yapar.
3. Transfer bitince DMA, CPU'ya interrupt gönderir.
- **Fly-by DMA**: veri DMA chip'inden geçmez; doğrudan I/O'dan memory'e gider.
- 8237 DMA chip: 4 bağımsız kanal.

### DCA (Direct Cache Access)
- 10 Gbps / 100 Gbps Ethernet'te DMA yetersiz kalır: paketler main memory'e yazılır, sonra cache'e çekilir → gereksiz kopyalama.
- **DCA / DDIO (Intel Direct Data I/O)**: gelen paketler doğrudan CPU cache'ine yazılır, main memory atlanır.
- Intel Xeon işlemcilerde uygulanmıştır.

### I/O Fonksiyonunun Evrimi (6 Aşama)
1. CPU, çevre birimini doğrudan kontrol eder.
2. Controller eklenir; programmed I/O, interrupt yok.
3. Aynı + interrupt eklenir → CPU verimliliği artar.
4. DMA eklenir → block transferler CPU'suz yapılır.
5. I/O module kendi instruction set'iyle bir processor haline gelir.
6. I/O module kendi local memory'sine sahip tam bir bilgisayar olur → minimal CPU müdahalesi.

### I/O Kanalları
- **Selector channel**: bir seferde tek yüksek hızlı cihaza hizmet verir.
- **Multiplexor channel**: aynı anda birden fazla yavaş cihaza hizmet verir.

### Dış Bağlantı Standartları
| Standart | Önemli Bilgi |
|---|---|
| **USB** | Varsayılan yavaş/orta hız periferal; ağaç topoloji; USB 3.1 = 10 Gbps |
| **FireWire (IEEE 1394)** | Daisy-chain; 63 cihaz; hot-plugging; otomatik konfigürasyon |
| **SCSI** | Paralel bus; 16–32 cihaz; enterprise storage |
| **Thunderbolt** | Intel+Apple; 10 Gbps çift yön + 10W güç; veri+video+ses tek kablo |
| **InfiniBand** | Yüksek uçlu sunucu; 64.000 cihaza kadar; storage area networking |
| **SATA** | Disk depolama için seri arayüz; 6 Gbps |
| **PCIe** | Yüksek hızlı periferal bus; cihaz başına 300 Mbps |
| **Ethernet** | Kablolu ağ; 100 Gbps'a kadar; switch tabanlı |
| **Wi-Fi (802.11ac)** | Kablosuz; 3.2 Gbps'a kadar |

---

## ÖZET FORMÜLLER

| Formül | Anlamı |
|---|---|
| `line = block mod m` | Direct-mapped cache: line numarası |
| `T_avg = h·T1 + (1−h)·T2` | İki seviyeli bellek ortalama erişim süresi |
| `Speedup = 1 / [(1−f) + f/N]` | Amdahl's Law |
| `N = λ · W` | Little's Law |
| `AM = Σxi / n` | Arithmetic Mean |
| `HM = n / Σ(1/xi)` | Harmonic Mean |
| `GM = (Π xi)^(1/n)` | Geometric Mean |
| `Access time = Seek + Rotational Latency + Transfer` | Disk erişim süresi |

---

## SÜRATTE HATIRLATICI — EN ÇOK ÇIKAN KONULAR

| Chapter | Odak Noktaları |
|---|---|
| **Ch1** | IAS register'ları, Moore's Law, ARM, embedded vs deeply embedded |
| **Ch2** | 5 performans tekniği, Amdahl formülü, AM/HM/GM ne zaman kullanılır, SPEC metrikleri |
| **Ch3** | Fetch-execute döngüsü, 4 interrupt türü, DMA tanımı, bus bileşenleri |
| **Ch4** | Temporal vs spatial locality, hit ratio formülü, access/cycle time farkı |
| **Ch5** | 3 mapping yöntemi (formül + adres bölümü), LRU/FIFO/LFU, write-through vs write-back |
| **Ch6** | DRAM vs SRAM karşılaştırması, ROM türleri (silme yöntemi), DDR SDRAM, Hamming SEC-DED |
| **Ch7** | Seek+latency+transfer, RAID 0–6 tablosu, SSD wear leveling, Blu-ray laser dalga boyu |
| **Ch8** | 3 I/O tekniği tablosu, programmed/interrupt/DMA farkları, memory-mapped vs isolated I/O |

---

*Başarılar! Chapter 5–8 birincil odak noktanız, Chapter 1–4 de kapsamda.*
