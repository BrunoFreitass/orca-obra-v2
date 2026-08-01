import cv2


def melhorar_imagem(caminho):
    """
    Melhora a qualidade da planta antes da IA.
    Retorna uma imagem OpenCV.
    """

    imagem = cv2.imread(caminho)

    if imagem is None:
        raise ValueError("Não foi possível abrir a imagem.")

    # escala de cinza
    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

    # remove pequenos ruídos
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # aumenta contraste
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    gray = clahe.apply(gray)

    return gray
