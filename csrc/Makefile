CC      = gcc
CFLAGS  = -std=c11 -O2 -Wall -Wextra -Iinclude
LDFLAGS = -lm

SRCDIR  = src
INCDIR  = include
OUTDIR  = output

# bkg2d CLI tool (library + frontend)
BKG2D_SRCS = $(SRCDIR)/bkg2d.c $(SRCDIR)/bkg2d_main.c
BKG2D_BIN  = bkg2d

# pst_background module (standalone)
PST_SRC = $(SRCDIR)/pst_background.c
PST_OBJ = $(SRCDIR)/pst_background.o

.PHONY: all clean run

all: $(BKG2D_BIN)

$(BKG2D_BIN): $(BKG2D_SRCS) $(INCDIR)/bkg2d.h
	$(CC) $(CFLAGS) -o $@ $(BKG2D_SRCS) $(LDFLAGS)

$(PST_OBJ): $(PST_SRC) $(INCDIR)/pst_background.h
	$(CC) $(CFLAGS) -c -o $@ $(PST_SRC)

run: $(BKG2D_BIN)
	./$(BKG2D_BIN)

clean:
	rm -f $(BKG2D_BIN) $(BKG2D_BIN).exe $(PST_OBJ)
	rm -f out_*.bmp out_*.bin
