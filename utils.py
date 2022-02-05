import numpy as np
import torch
import datetime
import torch.nn.functional as F

def make_timestamp():
    ISO_TIMESTAMP = "%Y%m%d_%H%M%S"
    return datetime.datetime.now().strftime(ISO_TIMESTAMP)
# Cosine learning rate scheduler.
#
# From https://github.com/valencebond/FixMatch_pytorch/blob/master/lr_scheduler.py
class WarmupCosineLrScheduler(torch.optim.lr_scheduler._LRScheduler):
    def __init__(
            self,
            optimizer,
            max_iter,
            warmup_iter,
            warmup_ratio=5e-4,
            warmup='exp',
            last_epoch=-1,
    ):
        self.max_iter = max_iter
        self.warmup_iter = warmup_iter
        self.warmup_ratio = warmup_ratio
        self.warmup = warmup
        super(WarmupCosineLrScheduler, self).__init__(optimizer, last_epoch)

    def get_lr(self):
        ratio = self.get_lr_ratio()
        lrs = [ratio * lr for lr in self.base_lrs]
        return lrs

    def get_lr_ratio(self):
        if self.last_epoch < self.warmup_iter:
            ratio = self.get_warmup_ratio()
        else:
            real_iter = self.last_epoch - self.warmup_iter
            real_max_iter = self.max_iter - self.warmup_iter
            ratio = np.cos((7 * np.pi * real_iter) / (16 * real_max_iter))
        return ratio

    def get_warmup_ratio(self):
        assert self.warmup in ('linear', 'exp')
        alpha = self.last_epoch / self.warmup_iter
        if self.warmup == 'linear':
            ratio = self.warmup_ratio + (1 - self.warmup_ratio) * alpha
        elif self.warmup == 'exp':
            ratio = self.warmup_ratio ** (1. - alpha)
        return ratio


# Recording Tools
class AverageMeter(object):
    """Computes and stores the average and current value
       Imported from https://github.com/pytorch/examples/blob/master/imagenet/main.py#L247-L262
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count

def predict_dataset_softmax(predict_loader, model, device, type='confidence'):
    model.eval()
    if type == 'confidence':
        softmax_outs = []
        with torch.no_grad():
            for images1, _, _ in predict_loader:
                images1 = images1.to(device)
                logits1 = model(images1)
                outputs = F.softmax(logits1, dim=1)
                softmax_outs.append(outputs)
        return torch.cat(softmax_outs, dim=0).to(device)
    else:
         loss_outs = torch.zeros(train_num).to(device)
         with torch.no_grad():
            for images1, label, idx in predict_loader:
                images1 = images1.to(device)
                logits1 = model(images1)
                loss = nn.CrossEntropyLoss(reduce=False)(logits1, label)
                loss_outs[idx] = loss
         return loss_outs
