from argparse import ArgumentParser
import numpy as np
import torch
import shutil
import time
from torchvision.transforms import Compose
from src.load_data import Dataset, Resize, ToTensor
from src.model import CNN
from pathlib import Path

def print_step(step: int, max_steps: int, loss: float, step_time: float):
    """ Prints information related to the current step
    Args:
        step (int): Current step (within the epoch)
        max_steps (int): Number of steps in the current epoch
        loss (float): Loss of current step
        step_time (float): Time it took to perform the whole step
        fetch_time (float): Time it took to load the data for the step
    """
    pre_string = f"{step}/{max_steps} ["
    post_string = (f"],  Loss: {loss.item():.3e}  -  Step time: {step_time:.2f}ms")
    terminal_cols = shutil.get_terminal_size(fallback=(156, 38)).columns
    progress_bar_len = min(terminal_cols - len(pre_string) - len(post_string)-1, 30)
    epoch_progress = int(progress_bar_len * (step/max_steps))
    print(pre_string + f"{epoch_progress*'='}>{(progress_bar_len-epoch_progress)*'.'}" + post_string,
            end=('\r' if step < max_steps else '\n'), flush=True)


def main():
    parser = ArgumentParser("Load Data")
    parser.add_argument("data_path", type=Path, help="path to dataset folder")
    parser.add_argument("--limit", "--l", type=int, help="limit of the dataset")
    args = parser.parse_args()

    transform=Compose([
        Resize(256,256),
        ToTensor()
    ])

    train_dataset = Dataset(args.data_path/"train", transform, args.limit)
    val_dataset = Dataset(args.data_path/"test", transform, args.limit)

    train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=8, shuffle=True, num_workers=8)
    val_dataloader = torch.utils.data.DataLoader(val_dataset, batch_size=8, shuffle=False, num_workers=8)

    model = CNN((256,256), 2)

    loss_fn = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=0.005)
    scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.998)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    max_step = (len(train_dataloader.dataset) + (8 - 1)) // 8

    for epoch in range(1000):
        epoch_loss = 0
        for step, batch in enumerate(train_dataloader):
            start_time = time.perf_counter()
            img_batch, label_batch = batch["img"].to(device).float(), batch["label"].to(device).long()
            optimizer.zero_grad()
            x = model(img_batch)
            loss = loss_fn(x, label_batch)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            print_step(step, max_step, loss, time.perf_counter() - start_time)
        print("")
        print(epoch_loss / max_step, flush=True)



if __name__ == "__main__":
    main()