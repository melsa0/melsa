# Documentation

Bu dizin, FPGA development için önemli dokümanları içerir.

## Yapı

```
docs/
├── datasheets/          # Board & chip datasheet/manual'ları
│   └── alinx/           # ALINX board dokümanları
├── xilinx/              # Xilinx/Vivado dokümanları
├── microchip/           # Microchip/Libero dokümanları
├── design_guides/       # Tasarım kılavuzları
├── tutorials/           # Tutorial'lar
├── best_practices/      # Best practices
└── README.md            # Bu dosya
```

## İçerik

### Datasheets
- **alinx/AXKU15_User_Manual.pdf** - ALINX AXKU15 Kintex UltraScale+ (XCKU15P) geliştirme kartı kullanım kılavuzu

### Xilinx Documentation
- UG guides özeti
- Vivado kullanım örnekleri
- GTH/GTY transceiver guides
- Memory controller guides
- PCIe implementation notes

### Microchip/PolarFire Documentation
- PolarFire SoC documentation
- Libero SoC usage guides
- Development kit examples
- RISC-V implementation guides

### Design Guides
- **uart_protocol_implementation.md** - UART 8N1 protocol, baud rate calculation, RX/TX design, common pitfalls
- **timing_closure_guide.md** - WNS/WHS analysis, fixing timing violations, registered BCD conversion
- **fsm_design_patterns.md** - State machine patterns: sequential, nested, string TX, priority arbiter, BCD
- **vga_timing_guide.md** - VGA 640x480 timing, pixel clock, pipeline architecture, text mode display
- **spi_protocol_guide.md** - SPI modes, clock generation, master state machine, common pitfalls
- CDC (Clock Domain Crossing) guidelines
- Verification strategies

### Tutorials
- **nexys_video_quickstart.md** - Nexys Video board setup, hybrid CLI/GUI workflow, pin constraints, common issues
- Step-by-step implementations
- Common design patterns

## Doküman Ekleme

Yeni doküman eklerken:

1. Uygun kategoriye yerleştirin
2. Markdown formatında olsun (.md)
3. Clear başlıklar ve örnekler ekleyin
4. Kaynak referansları ekleyin

## RAG Entegrasyonu

Bu dizindeki tüm markdown dosyaları otomatik olarak RAG veritabanına eklenir:

```bash
python shared/build_rag_database.py
```

## Doküman Formatı

Önerilen format:

```markdown
# Başlık

## Özet
Kısa açıklama

## Detaylı Açıklama
...

## Kod Örnekleri
```verilog
// Verilog code
```

## Referanslar
- [Link 1]
- [Link 2]
```
