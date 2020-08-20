import streamlit as st
import PIL, requests
from mantisshrimp.all import *
from PIL import Image
from random import randrange

index = -1
MASK_PENNFUNDAN_WEIGHTS_URL = "https://mantisshrimp-models.s3.us-east-2.amazonaws.com/pennfundan_maskrcnn_resnet50fpn.zip"
FASTER_PETS_WEIGHTS_URL = "https://github.com/airctic/streamlitshrimp/releases/download/pets_faster_resnetfpn50/pets_faster_resnetfpn50.zip"


pennfundan_images = [
    "https://raw.githubusercontent.com/ai-fast-track/ice-streamlit/master/images/kids_crossing_street.jpg",
    "https://raw.githubusercontent.com/ai-fast-track/ice-streamlit/master/images/image0.png",
    "https://raw.githubusercontent.com/ai-fast-track/ice-streamlit/master/images/image1.png",
    "https://raw.githubusercontent.com/ai-fast-track/ice-streamlit/master/images/image2.png",
    "https://raw.githubusercontent.com/ai-fast-track/ice-streamlit/master/images/image3.png",
    "https://raw.githubusercontent.com/ai-fast-track/ice-streamlit/master/images/image4.png",
    "https://raw.githubusercontent.com/ai-fast-track/ice-streamlit/master/images/image5.png",
    "https://www.adventisthealth.org/cms/thumbnails/00/1100x506/images/blog/kids_crossing_street.jpg",
    "https://i.cbc.ca/1.5510620.1585229177!/cumulusImage/httpImage/image.jpg_gen/derivatives/16x9_780/toronto-street-scene-covid-19.jpg",
]


def sidebar_ui():
    # st.sidebar.image("images/airctic-logo-medium.png")
    st.sidebar.image(
        "https://raw.githubusercontent.com/ai-fast-track/ice-streamlit/master/images/icevision-deploy-small.png"
    )


# This sidebar UI lets the user select model thresholds.
def object_detector_ui():
    # st.sidebar.markdown("# Model Thresholds")
    detection_threshold = st.sidebar.slider("Detection threshold", 0.0, 1.0, 0.5, 0.01)
    mask_threshold = st.sidebar.slider("Mask threshold", 0.0, 1.0, 0.5, 0.01)
    return detection_threshold, mask_threshold


@st.cache(allow_output_mutation=True)
def load_model(model_name="mask_rcnn", class_map=class_map, url=None):
    if url is None:
        print("Please provide a valid URL")
        return None
    else:
        if model_name == "mask_rcnn":
            model = mask_rcnn.model(num_classes=len(class_map))
        if model_name == "faster_rcnn":
            model = faster_rcnn.model(num_classes=len(class_map))
        if model_name == "effecientdet":
            model = effecientdet.model(num_classes=len(class_map))

        state_dict = torch.hub.load_state_dict_from_url(
            url, map_location=torch.device("cpu")
        )
        model.load_state_dict(state_dict)
        print(f"url: {url}")
        return model


def image_from_url(url):
    res = requests.get(url, stream=True)
    img = PIL.Image.open(res.raw)
    return np.array(img)


def predict(
    model, image_url, detection_threshold: float = 0.5, mask_threshold: float = 0.5
):
    img = image_from_url(image_url)

    tfms_ = tfms.A.Adapter([tfms.A.Normalize()])
    # Whenever you have images in memory (numpy arrays) you can use `Dataset.from_images`
    infer_ds = Dataset.from_images([img], tfms_)

    batch, samples = mask_rcnn.build_infer_batch(infer_ds)
    preds = mask_rcnn.predict(
        model=model,
        batch=batch,
        detection_threshold=detection_threshold,
        mask_threshold=mask_threshold,
    )

    return samples[0]["img"], preds[0]


def show_prediction(
    img, pred, class_map=class_map, bbox=False, image_key="image_key",
):
    show_pred(
        img=img,
        pred=pred,
        class_map=class_map,
        denormalize_fn=denormalize_imagenet,
        show=True,
        bbox=bbox,
    )

    # Grab image from the current matplotlib figure
    fig = plt.gcf()
    fig.canvas.draw()
    fig_arr = np.array(fig.canvas.renderer.buffer_rgba())

    st.image(fig_arr, use_column_width=True, image_key=image_key)


def run_app(index=index):
    # st.image("images/icevision.png", use_column_width=True)
    sidebar_ui()

    page = st.sidebar.selectbox(
        "Choose a dataset", ["PennFundan", "PETS", "Fridge Objects", "Raccoon"]
    )

    # Draw the threshold parameters for object detection model.
    detection_threshold, mask_threshold = object_detector_ui()

    bbox = st.sidebar.checkbox(label="Bounding Box", value=False)
    print("bbox", bbox)

    st.sidebar.image("images/airctic-logo-medium.png")

    st.markdown("### ** Paste Your Image URL**")
    my_placeholder = st.empty()

    # if 'index' in globals():
    if index == -1:
        index = 0
        print("index: ", index)
    image_path = pennfundan_images[index]
    image_url_key = f"image_url_key-{index}"
    image_url = my_placeholder.text_input(label="", value=image_path, key=image_url_key)

    st.markdown("### **Or**")
    if st.button("Press Me!"):
        # Just load an image from sample_images folder
        index = randrange(len(pennfundan_images))
        image_path = pennfundan_images[index]
        image_url_key = f"image_url_key-{index}"
        image_url = my_placeholder.text_input(
            label="", value=image_path, key=image_url_key
        )

    if page == "PennFundan":
        print("PennFundan")
        class_map = datasets.pennfundan.class_map()
        model = load_model(
            model_name="mask_rcnn", class_map=class_map, url=MASK_PENNFUNDAN_WEIGHTS_URL
        )

    if page == "PETS":
        print("PETS")
        class_map = datasets.pets.class_map()
        model = load_model(
            model_name="faster_rcnn", class_map=class_map, url=FASTER_PETS_WEIGHTS_URL
        )

    # print(MASK_PENNFUNDAN_WEIGHTS_URL)
    # class_map = datasets.pennfundan.class_map()
    # model = load_model(
    #     model_name="mask_rcnn", class_map=class_map, url=MASK_PENNFUNDAN_WEIGHTS_URL
    # )

    image_key = f"image_key-{index}"
    if image_url:
        img, pred = predict(
            model=model,
            image_url=image_url,
            detection_threshold=detection_threshold,
            mask_threshold=mask_threshold,
        )
        show_prediction(
            img=img, pred=pred, class_map=class_map, bbox=bbox, image_key=image_key
        )


if __name__ == "__main__":
    index = -1
    run_app(index=index)
