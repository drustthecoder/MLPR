import numpy
from mlFunc import *
from GMM import *


def kfold_cross(func, DTR, LTR, k):
    accuracy = []
    Dtr = numpy.split(DTR, k, axis=1)
    Ltr = numpy.split(LTR, k)

    for i in range(k):
        D = []
        L = []
        if i == 0:
            D.append(numpy.hstack(Dtr[i + 1:]))
            L.append(numpy.hstack(Ltr[i + 1:]))
        elif i == k - 1:
            D.append(numpy.hstack(Dtr[:i]))
            L.append(numpy.hstack(Ltr[:i]))
        else:
            D.append(numpy.hstack(Dtr[:i]))
            D.append(numpy.hstack(Dtr[i + 1:]))
            L.append(numpy.hstack(Ltr[:i]))
            L.append(numpy.hstack(Ltr[i + 1:]))

        D = numpy.hstack(D)
        L = numpy.hstack(L)

        DTE = Dtr[i]
        LTE = Ltr[i]
        # print(str(DTE) + " " + str(i))
        _, lpred = func(DTE, D, L)
        acc, _ = test(LTE, lpred)
        accuracy.append(acc)

    return numpy.mean(accuracy)


def holdout_validation(func, D, L, seed=0, trainPerc=0.8):
    nTrain = int(D.shape[1] * trainPerc)
    numpy.random.seed(seed)
    idx = numpy.random.permutation(D.shape[1])
    idxTrain = idx[0:nTrain]
    idxTest = idx[nTrain:]
    DTR = D[:, idxTrain]
    DTE = D[:, idxTest]
    LTR = L[idxTrain]
    LTE = L[idxTest]

    _, lpred = func(DTE, DTR, LTR)
    acc, _ = test(LTE, lpred)

    return acc


def leave_one_out(func, DTR, LTR):
    accuracy = []

    for i in range(DTR.shape[1]):
        D = []
        L = []
        D.append(DTR[:, :i])
        D.append(DTR[:, i + 1:])
        D = numpy.hstack(D)

        L.append(LTR[:i])
        L.append(LTR[i + 1:])
        L = numpy.hstack(L)

        DTE = DTR[:, i]
        LTE = LTR[i]
        # print(str(DTE) + " " + str(i))
        _, lpred = func(mcol(DTE), D, L)
        acc, _ = test(LTE, lpred)
        accuracy.append(acc)
    return numpy.mean(accuracy)


def confusion_matrix(Lpred, LTE, k=2):
    # k = number of classes
    conf = numpy.zeros((k, k))
    for i in range(k):
        for j in range(k):
            conf[i][j] = ((Lpred == i) * (LTE == j)).sum()
    return conf


def assign_labels(scores, pi, Cfn, Cfp, th=None):
    if th is None:
        th = -numpy.log(pi * Cfn) + numpy.log((1 - pi) * Cfp)
    P = scores > th
    return numpy.int32(P)


def confusion_matrix_binary(Lpred, LTE):
    C = numpy.zeros((2, 2))
    C[0, 0] = ((Lpred == 0) * (LTE == 0)).sum()
    C[0, 1] = ((Lpred == 0) * (LTE == 1)).sum()
    C[1, 0] = ((Lpred == 1) * (LTE == 0)).sum()
    C[1, 1] = ((Lpred == 1) * (LTE == 1)).sum()
    return C


def compute_emp_Bayes_binary(CM, pi, Cfn, Cfp):
    fnr = CM[0, 1] / (CM[0, 1] + CM[1, 1])
    fpr = CM[1, 0] / (CM[0, 0] + CM[1, 0])
    return pi * Cfn * fnr + (1 - pi) * Cfp * fpr


def compute_normalized_emp_Bayes(CM, pi, Cfn, Cfp):
    empBayes = compute_emp_Bayes_binary(CM, pi, Cfn, Cfp)
    return empBayes / min(pi * Cfn, (1 - pi) * Cfp)


def compute_act_DCF(scores, labels, pi, Cfn, Cfp, th=None):
    Pred = assign_labels(scores, pi, Cfn, Cfp, th=th)
    CM = confusion_matrix_binary(Pred, labels)
    return compute_normalized_emp_Bayes(CM, pi, Cfn, Cfp)


def compute_min_DCF(scores, labels, pi, Cfn, Cfp):
    t = numpy.array(scores)
    t.sort()
    numpy.concatenate([numpy.array([-numpy.inf]), t, numpy.array([numpy.inf])])
    dcfList = []
    for _th in t:
        dcfList.append(compute_act_DCF(scores, labels, pi, Cfn, Cfp, th=_th))
    return numpy.array(dcfList).min()


def bayes_error_plot(pArray, scores, labels, minCost=False, th=None):
    y = []
    for p in pArray:
        pi = 1.0 / (1.0 + numpy.exp(-p))
        if minCost:
            y.append(compute_min_DCF(scores, labels, pi, 1, 1))
        else:
            y.append(compute_act_DCF(scores, labels, pi, 1, 1, th))
    return numpy.array(y)

def bayes_error_plot_compare(pi, scores, labels):
    y = []
#    pi = 1.0 / (1.0 + numpy.exp(-pi))
    y.append(compute_min_DCF(scores, labels, pi, 1, 1))
    return numpy.array(y)


def bayes_error_min_act_plot(D, LTE, title, ylim):
    p = numpy.linspace(-3, 3, 21)
    pylab.title(title)
    pylab.plot(p, bayes_error_plot(p, D, LTE, minCost=False), color='r')
    pylab.plot(p, bayes_error_plot(p, D, LTE, minCost=True), color='b')
    pylab.ylim(0, ylim)
    pylab.savefig('./images/DCF_' + title + '.svg')
    pylab.show()


def plot_DCF(x, y, xlabel, title, base=10):
    plt.figure()
    plt.plot(x, y[0], label= 'min DCF prior=0.5', color='b')
    plt.plot(x, y[1], label= 'min DCF prior=0.9', color='g')
    plt.plot(x, y[2], label= 'min DCF prior=0.1', color='r')
    plt.xlim([min(x), max(x)])
    plt.xscale("log", base=base)
    plt.legend([ "min DCF prior=0.5", "min DCF prior=0.9", "min DCF prior=0.1"])
    plt.xlabel(xlabel)
    plt.ylabel("min DCF")
    plt.savefig('./images/DCF_' + title+ '.svg')
    plt.show()
    return

def plot_DCF_for_SVM_RBF_calibration(x, y, xlabel, title, base=10):
    plt.figure()
    plt.plot(x, y[0], label= 'logγ=-3', color='b')
    plt.plot(x, y[1], label= 'logγ=-2', color='g')
    plt.plot(x, y[2], label= 'logγ=-1', color='r')
    plt.plot(x, y[3], label= 'logγ=-0', color='y')

    plt.xlim([min(x), max(x)])
    plt.ylim([0.0, 0.7])
    plt.xscale("log", base=base)
    plt.legend([ "logγ=-3", "logγ=-2", "logγ=-1", "logγ=0"])
    plt.xlabel(xlabel)
    plt.ylabel("minDCF")
    plt.savefig('./images/DCF_' + title+ '.svg')
    plt.show()
    return


def plot_ROC(llrs, LTE, title):
    thresholds = numpy.array(llrs)
    thresholds.sort()
    thresholds = numpy.concatenate([numpy.array([-numpy.inf]), thresholds, numpy.array([numpy.inf])])
    FPR = numpy.zeros(thresholds.size)
    TPR = numpy.zeros(thresholds.size)
    for idx, t in enumerate(thresholds):
        Pred = numpy.int32(llrs > t)
        conf = confusion_matrix_binary(Pred, LTE)
        TPR[idx] = conf[1, 1] / (conf[1, 1] + conf[0, 1])
        FPR[idx] = conf[1, 0] / (conf[1, 0] + conf[0, 0])
    pylab.plot(FPR, TPR)
    pylab.title(title)
    pylab.savefig('./images/ROC_' + title + '.png')
    pylab.show()


def generative_acc_err(DTE, DTR, LTE, LTR, title):
    _, LPred2, llrs = MVG(DTE, DTR, LTR)
    _, LP2n, llrsn = naive_MVG(DTE, DTR, LTR)
    _, LP2t, llrst = tied_cov_GC(DTE, DTR, LTR)
    _, LP2nt, llrsnt = tied_cov_naive_GC(DTE, DTR, LTR)
    # logMVG accuracy
    log_acc, log_err = test(LTE, LPred2)
    log_acc_n, log_err_n = test(LTE, LP2n)
    log_acc_t, log_err_t = test(LTE, LP2t)
    log_acc_nt, log_err_nt = test(LTE, LP2nt)

    table = PrettyTable(["", "Accuracy %", "Error "])
    table.title = title
    table.add_row(["MVG", round(log_acc * 100, 3), round(log_err * 100, 3)])
    table.add_row(["Naive MVG", round(log_acc_n * 100, 3), round(log_err_n * 100, 3)])
    table.add_row(["Tied GC", round(log_acc_t * 100, 3), round(log_err_t * 100, 3)])
    table.add_row(["Naive Tied GC", round(log_acc_nt * 100, 3), round(log_err_nt * 100, 3)])
    print(table)
