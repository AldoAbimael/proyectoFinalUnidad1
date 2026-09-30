import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable
from PIL import Image, ImageTk, ImageDraw
from models.usuario import Usuario
from services.usuario_service import UsuarioService
from services.exceptions import BusinessError, ValidationError


class AvatarWidget(tk.Canvas):
    """
    Componente visual para la Foto de Perfil del Usuario.
    Renderiza un avatar circular estilizado (usando Pillow).
    Permite hacer clic para seleccionar y cargar una nueva imagen (.png, .jpg) desde la computadora.
    """

    def __init__(
        self,
        parent: tk.Widget,
        usuario: Usuario,
        usuario_service: UsuarioService,
        size: int = 46,
        on_avatar_updated: Optional[Callable[[str], None]] = None,
        bg_color: str = "#1e293b"
    ):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=bg_color,
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )
        self.usuario = usuario
        self.usuario_service = usuario_service
        self.size = size
        self.on_avatar_updated = on_avatar_updated
        self.bg_color = bg_color
        self._photo_image = None  # Mantener referencia viva para evitar recolección de basura

        self.bind("<Button-1>", lambda e: self.seleccionar_nueva_foto())
        self.cargar_avatar()

    def set_bg(self, new_bg: str) -> None:
        """Actualiza el color de fondo del canvas si cambia el tema."""
        self.bg_color = new_bg
        self.configure(bg=new_bg)
        self.cargar_avatar()

    def cargar_avatar(self) -> None:
        """Carga y dibuja la imagen de perfil actual o genera el avatar por defecto."""
        self.delete("all")
        ruta = self.usuario.avatar_path

        img = None
        if ruta and os.path.exists(ruta):
            try:
                img = Image.open(ruta).convert("RGBA")
            except Exception:
                img = None

        if img is None:
            # Generar avatar circular estilizado con la inicial del usuario
            img = self._generar_avatar_defecto()

        # Recortar en círculo perfecto con suavizado
        img_circular = self._crear_recorte_circular(img, self.size)
        self._photo_image = ImageTk.PhotoImage(img_circular)

        # Dibujar en el canvas
        self.create_image(self.size // 2, self.size // 2, image=self._photo_image)

    def _generar_avatar_defecto(self) -> Image.Image:
        """Genera una imagen con inicial estilizada y color representativo según el rol."""
        dim = self.size * 2  # Supersampling para mayor nitidez
        color_fondo = (30, 58, 138, 255) if self.usuario.es_admin else (2, 132, 199, 255)
        
        img = Image.new("RGBA", (dim, dim), color_fondo)
        draw = ImageDraw.Draw(img)

        # Letra inicial del usuario
        inicial = (self.usuario.username[:1] if self.usuario.username else "U").upper()
        
        # Dibujar círculo decorativo interior
        draw.ellipse((4, 4, dim - 4, dim - 4), outline=(255, 255, 255, 120), width=4)
        
        # Dibujar inicial si es posible
        try:
            from PIL import ImageFont
            font = ImageFont.load_default(size=dim // 2)
            bbox = draw.textbbox((0, 0), inicial, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            draw.text(((dim - w) / 2, (dim - h) / 2 - 4), inicial, fill=(255, 255, 255, 255), font=font)
        except Exception:
            pass

        return img

    def _crear_recorte_circular(self, im: Image.Image, tam: int) -> Image.Image:
        """Reescala y aplica una máscara circular con borde elegante."""
        # Redimensionar al tamaño deseado manteniendo proporción
        im = im.resize((tam, tam), Image.Resampling.LANCZOS)

        # Máscara circular
        mask = Image.new("L", (tam, tam), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, tam - 1, tam - 1), fill=255)

        # Salida con transparencia
        output = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
        output.paste(im, (0, 0), mask=mask)

        # Dibujar borde fino decorativo
        draw_border = ImageDraw.Draw(output)
        draw_border.ellipse((0, 0, tam - 1, tam - 1), outline=(255, 255, 255, 200), width=2)

        return output

    def seleccionar_nueva_foto(self) -> None:
        """Abre un diálogo de selección de archivo para actualizar la foto de perfil."""
        archivo = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            title="Seleccionar Foto de Perfil",
            filetypes=[
                ("Imágenes compatibles", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"),
                ("Archivos PNG", "*.png"),
                ("Archivos JPG / JPEG", "*.jpg;*.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not archivo:
            return

        try:
            nueva_ruta = self.usuario_service.guardar_avatar(self.usuario, archivo)
            self.cargar_avatar()
            messagebox.showinfo(
                "Foto de Perfil Actualizada",
                f"Tu foto de perfil se ha actualizado correctamente.",
                parent=self.winfo_toplevel()
            )
            if self.on_avatar_updated:
                self.on_avatar_updated(nueva_ruta)
        except (ValidationError, BusinessError) as e:
            messagebox.showerror("Error al Cargar Imagen", str(e), parent=self.winfo_toplevel())
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al procesar la imagen: {e}", parent=self.winfo_toplevel())
