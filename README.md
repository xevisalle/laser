# LASER: Lightweight And SEcure Remote keyless entry protocol 

This is an implementation of a security protocol for Remote Keyless Entry (RKE) systems, published in Proceedings of SECRYPT 2019. This solution has been submitted as **an invention to be patented with European Patent application number 19382339.0**, on May 6th, 2019. 

The paper with full details regarding this invention can be found [here](https://arxiv.org/pdf/1905.05694.pdf).

**DISCLAIMER:** this implementation is currently **unstable**, it is not intended to be used in a production environment, only for academic purposes.


## Overview

In order to be used, the implemented protocol requires two units of the [YARD Stick One](https://greatscottgadgets.com/yardstickone/). One of them will act as a key fob, and the other one as a device we want to control. Like this, the device could implement different functions to be performed, and the fob will authenticate its owner.

## Usage

First install the **rflib** module for python, found in the [RfCat](https://github.com/atlas0fd00m/rfcat) project, and also the [Blake2](https://blake2.net/) module:

```
git clone https://github.com/atlas0fd00m/rfcat
cd rfcat
sudo python setup.py
pip install pyblake2
```
Now you can get the help by executing:

```
git clone https://github.com/xevisalle/laser.git
cd laser
sudo python laser.py
```

## Authors

* Vanesa Daza - vanesa.daza@upf.edu
* Xavier Salleras - xavier.salleras@upf.edu
